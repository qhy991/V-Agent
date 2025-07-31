#!/usr/bin/env python3
"""
基础智能体类 - 支持Function Calling和文件操作

Base Agent with Function Calling and File Operations
"""

import asyncio
import logging
import os
import json
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .enums import AgentCapability, AgentStatus
from .response_format import (
    StandardizedResponse, ResponseBuilder, ResponseFormat, 
    TaskStatus, ResponseType, QualityMetrics,
    create_success_response, create_error_response, create_progress_response
)
from tools.tool_registry import ToolRegistry, ToolPermission
from .agent_prompts import agent_prompt_manager
from .function_calling import ToolCall, ToolResult
from .enhanced_logging_config import get_component_logger, get_artifacts_dir


@dataclass
class FileReference:
    """文件引用"""
    file_path: str
    file_type: str  # "verilog", "testbench", "report", "config"
    description: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_type": self.file_type,
            "description": self.description,
            "metadata": self.metadata or {}
        }


@dataclass
class TaskMessage:
    """任务消息 - 支持文件路径传递"""
    task_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    content: str
    file_references: List[FileReference] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type,
            "content": self.content,
            "file_references": [ref.to_dict() for ref in (self.file_references or [])],
            "metadata": self.metadata or {}
        }


class BaseAgent(ABC):
    """基础智能体类 - 支持Function Calling"""
    
    def __init__(self, agent_id: str, role: str = None, capabilities: Set[AgentCapability] = None):
        self.agent_id = agent_id
        self.role = role or "base_agent"
        self._capabilities = capabilities or set()
        self.status = AgentStatus.IDLE
        
        # 设置日志 - 使用增强日志系统
        self.logger = get_component_logger('base_agent', f"Agent.{self.agent_id}")
        
        # 获取全局工件目录（如果已初始化）
        try:
            self.default_artifacts_dir = get_artifacts_dir()
        except:
            self.default_artifacts_dir = Path("./output")
        
        # Function Calling工具注册表 (新的方式)
        self.function_calling_registry = {}
        self.function_descriptions = {}
        
        # 传统工具调用系统 (保持兼容性)
        self.tool_registry = ToolRegistry()
        self.enable_tool_calling()
        
        # 文件缓存
        self.file_cache: Dict[str, str] = {}
        self.file_metadata_cache: Dict[str, Dict] = {}
        
        # 任务历史
        self.task_history: List[Dict[str, Any]] = []
        
        # Function Calling配置
        self.max_tool_retry_attempts = 3
        self.tool_failure_contexts: List[Dict[str, Any]] = []
        
        # 注册Function Calling工具
        self._register_function_calling_tools()
        
        # 生成system prompt (包含工具信息)
        self.system_prompt = self._build_enhanced_system_prompt()
        
        self.logger.info(f"✅ {self.__class__.__name__} (Function Calling支持) 初始化完成")
        self.logger.debug(f"📝 System prompt 长度: {len(self.system_prompt)} 字符")
    
    def _register_function_calling_tools(self):
        """注册Function Calling工具 - 子类可以重写"""
        # 基础文件操作工具
        self.register_function_calling_tool(
            name="write_file",
            func=self._tool_write_file,
            description="将内容写入到文件",
            parameters={
                "filename": {"type": "string", "description": "文件名", "required": True},
                "content": {"type": "string", "description": "文件内容", "required": True},
                "directory": {"type": "string", "description": "目录路径", "required": False}
            }
        )
        
        self.register_function_calling_tool(
            name="read_file",
            func=self._tool_read_file,
            description="读取文件内容",
            parameters={
                "filepath": {"type": "string", "description": "文件路径", "required": True}
            }
        )
    
    def register_function_calling_tool(self, name: str, func, description: str, parameters: Dict[str, Any] = None):
        """注册Function Calling工具"""
        self.function_calling_registry[name] = func
        self.function_descriptions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters or {}
        }
        self.logger.info(f"🔧 注册Function Calling工具: {name}")
    
    def enable_tool_calling(self):
        """启用工具调用能力"""
        # 根据能力设置权限
        permissions = {ToolPermission.READ_ONLY}
        
        if AgentCapability.CODE_GENERATION in self._capabilities:
            permissions.add(ToolPermission.WRITE_FILES)
            permissions.add(ToolPermission.EXECUTE_SAFE)
            permissions.add(ToolPermission.DATABASE_READ)
        
        if AgentCapability.TASK_COORDINATION in self._capabilities:
            permissions.add(ToolPermission.WRITE_FILES)
            permissions.add(ToolPermission.EXECUTE_SAFE)
            permissions.add(ToolPermission.DATABASE_READ)
            permissions.add(ToolPermission.DATABASE_WRITE)
        
        if AgentCapability.TEST_GENERATION in self._capabilities:
            permissions.add(ToolPermission.DATABASE_READ)
            
        if AgentCapability.CODE_REVIEW in self._capabilities:
            permissions.add(ToolPermission.DATABASE_READ)
        
        if AgentCapability.SPECIFICATION_ANALYSIS in self._capabilities:
            permissions.add(ToolPermission.DATABASE_READ)
        
        self.allowed_permissions = permissions
        self.logger.info(f"🛠️ 传统工具调用已启用: 权限={len(permissions)}")
    
    def _build_enhanced_system_prompt(self) -> str:
        """构建包含Function Calling信息的增强system prompt"""
        base_prompt = agent_prompt_manager.get_system_prompt(self.role, self._capabilities)
        
        if not self.function_descriptions:
            return base_prompt
        
        tools_info = "\n\n## 🛠️ 可用工具\n\n"
        tools_info += "你可以通过以下JSON格式调用工具：\n"
        tools_info += "```json\n{\n    \"tool_calls\": [\n        {\n            \"tool_name\": \"工具名称\",\n"
        tools_info += "            \"parameters\": {\n                \"参数名\": \"参数值\"\n            }\n        }\n    ]\n}\n```\n\n"
        tools_info += "### 可用工具列表:\n\n"
        
        for tool_name, desc in self.function_descriptions.items():
            tools_info += f"**{tool_name}**: {desc['description']}\n"
            if desc.get('parameters'):
                tools_info += "参数:\n"
                for param_name, param_info in desc['parameters'].items():
                    param_desc = param_info.get('description', '无描述')
                    param_type = param_info.get('type', 'string')
                    required = "必需" if param_info.get('required', False) else "可选"
                    tools_info += f"  - {param_name} ({param_type}): {param_desc} [{required}]\n"
            tools_info += "\n"
        
        tools_info += "### 工具调用规则:\n"
        tools_info += "1. 当需要执行特定操作时，使用JSON格式调用相应工具\n"
        tools_info += "2. 等待工具执行结果后再继续\n"
        tools_info += "3. 如果工具调用失败，分析错误原因并调整参数重试\n"
        tools_info += "4. 根据工具结果做出下一步决策\n\n"
        
        return base_prompt + tools_info
    
    # ==========================================================================
    # 🔧 Function Calling 核心方法
    # ==========================================================================
    
    async def process_with_function_calling(self, user_request: str, max_iterations: int = 10) -> str:
        """使用Function Calling处理用户请求"""
        self.logger.info(f"🚀 开始Function Calling处理: {user_request[:100]}...")
        
        # 构建对话历史
        conversation = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_request}
        ]
        
        for iteration in range(max_iterations):
            self.logger.info(f"🔄 Function Calling 迭代 {iteration + 1}/{max_iterations}")
            
            try:
                # 调用LLM
                llm_response = await self._call_llm_for_function_calling(conversation)
                
                # 解析工具调用
                tool_calls = self._parse_tool_calls_from_response(llm_response)
                
                if not tool_calls:
                    # 没有工具调用，返回最终结果
                    self.logger.info("✅ 任务完成，无需调用工具")
                    return llm_response
                
                # 执行工具调用
                conversation.append({"role": "assistant", "content": llm_response})
                
                all_tool_results = []
                for tool_call in tool_calls:
                    result = await self._execute_tool_call_with_retry(tool_call)
                    all_tool_results.append(result)
                
                # 构建工具结果消息
                result_message = self._format_tool_results(tool_calls, all_tool_results)
                conversation.append({"role": "user", "content": result_message})
                
            except Exception as e:
                self.logger.error(f"❌ Function Calling迭代失败: {str(e)}")
                return f"处理请求时发生错误: {str(e)}"
        
        # 达到最大迭代次数，获取最终响应
        try:
            final_response = await self._call_llm_for_function_calling(conversation)
            return final_response
        except Exception as e:
            return f"无法完成请求，已达到最大迭代次数: {str(e)}"
    
    def _parse_tool_calls_from_response(self, response: str) -> List[ToolCall]:
        """解析LLM响应中的工具调用"""
        tool_calls = []
        
        try:
            # 方法1: 直接解析JSON格式
            cleaned_response = response.strip()
            if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                data = json.loads(cleaned_response)
                if 'tool_calls' in data and isinstance(data['tool_calls'], list):
                    for tool_call_data in data['tool_calls']:
                        if isinstance(tool_call_data, dict) and 'tool_name' in tool_call_data:
                            tool_call = ToolCall(
                                tool_name=tool_call_data['tool_name'],
                                parameters=tool_call_data.get('parameters', {}),
                                call_id=tool_call_data.get('call_id', f"call_{len(tool_calls)}")
                            )
                            tool_calls.append(tool_call)
                            self.logger.info(f"🔧 解析到工具调用: {tool_call.tool_name}")
            
            # 方法2: 查找JSON代码块
            if not tool_calls:
                json_pattern = r'```json\s*(\{.*?\})\s*```'
                matches = re.findall(json_pattern, response, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if 'tool_calls' in data:
                            for tool_call_data in data['tool_calls']:
                                tool_call = ToolCall(
                                    tool_name=tool_call_data['tool_name'],
                                    parameters=tool_call_data.get('parameters', {}),
                                    call_id=tool_call_data.get('call_id', f"call_{len(tool_calls)}")
                                )
                                tool_calls.append(tool_call)
                    except json.JSONDecodeError:
                        continue
            
            # 方法3: 文本模式匹配备用方案
            if not tool_calls:
                tool_patterns = [
                    r'调用工具\s*[：:]\s*(\w+)',
                    r'使用工具\s*[：:]\s*(\w+)',
                    r'tool[：:]\s*(\w+)',
                    r'function[：:]\s*(\w+)'
                ]
                
                for pattern in tool_patterns:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    for match in matches:
                        tool_call = ToolCall(
                            tool_name=match,
                            parameters={},
                            call_id=f"call_{len(tool_calls)}"
                        )
                        tool_calls.append(tool_call)
                        self.logger.info(f"🔧 从文本中解析到工具调用: {tool_call.tool_name}")
            
            return tool_calls
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"⚠️ JSON解析失败: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"❌ 工具调用解析失败: {str(e)}")
            return []
    
    async def _execute_tool_call_with_retry(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用，支持失败重试和LLM反馈"""
        last_error = None
        
        for attempt in range(self.max_tool_retry_attempts):
            try:
                self.logger.info(f"🔧 执行工具调用: {tool_call.tool_name} (尝试 {attempt + 1}/{self.max_tool_retry_attempts})")
                
                # 检查工具是否存在
                if tool_call.tool_name not in self.function_calling_registry:
                    return ToolResult(
                        call_id=tool_call.call_id or "unknown",
                        success=False,
                        result=None,
                        error=f"工具 '{tool_call.tool_name}' 不存在。可用工具: {list(self.function_calling_registry.keys())}"
                    )
                
                # 获取并执行工具函数
                tool_func = self.function_calling_registry[tool_call.tool_name]
                
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**tool_call.parameters)
                else:
                    result = tool_func(**tool_call.parameters)
                
                self.logger.info(f"✅ 工具执行成功: {tool_call.tool_name}")
                return ToolResult(
                    call_id=tool_call.call_id or "unknown",
                    success=True,
                    result=result,
                    error=None
                )
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"⚠️ 工具执行失败 {tool_call.tool_name} (尝试 {attempt + 1}): {str(e)}")
                
                # 记录详细的失败上下文，用于LLM分析和智能重试
                failure_context = {
                    "tool_name": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "attempt": attempt + 1,
                    "timestamp": time.time(),
                    "agent_id": self.agent_id,
                    "role": self.role
                }
                
                # 增强错误信息格式
                detailed_error = await self._enhance_error_with_context(failure_context)
                failure_context["detailed_error"] = detailed_error
                
                self.tool_failure_contexts.append(failure_context)
                
                # 如果是最后一次尝试，记录完整错误链
                if attempt == self.max_tool_retry_attempts - 1:
                    self.logger.error(f"❌ 工具调用最终失败 {tool_call.tool_name}: {last_error}")
                    self.logger.error(f"📊 失败上下文: {json.dumps(failure_context, indent=2, default=str)}")
                else:
                    # 使用LLM分析错误并提供重试建议
                    retry_advice = await self._get_llm_retry_advice(failure_context)
                    self.logger.info(f"💡 重试建议: {retry_advice}")
                    await asyncio.sleep(1)
        
        # 所有重试都失败了，返回增强的错误信息
        return ToolResult(
            call_id=tool_call.call_id or "unknown",
            success=False,
            result=None,
            error=f"工具执行失败 (已重试{self.max_tool_retry_attempts}次): {last_error}",
            context={"failure_chain": self.tool_failure_contexts}
        )
    
    def _format_tool_results(self, tool_calls: List[ToolCall], tool_results: List[ToolResult]) -> str:
        """格式化工具执行结果"""
        result_message = "## 工具执行结果\n\n"
        
        for tool_call, tool_result in zip(tool_calls, tool_results):
            if tool_result.success:
                result_message += f"### ✅ {tool_call.tool_name} - 执行成功\n"
                result_message += f"**结果**: {tool_result.result}\n\n"
            else:
                result_message += f"### ❌ {tool_call.tool_name} - 执行失败\n"
                result_message += f"**错误**: {tool_result.error}\n"
                result_message += f"**建议**: 请分析错误原因并调整参数重新调用\n\n"
        
        # 如果有失败的工具调用，添加重试建议
        failed_calls = [tc for tc, tr in zip(tool_calls, tool_results) if not tr.success]
        if failed_calls:
            result_message += "### 🔄 重试建议\n"
            result_message += "对于失败的工具调用，请:\n"
            result_message += "1. 检查参数是否正确\n"
            result_message += "2. 确认文件路径是否存在\n"
            result_message += "3. 调整参数后重新调用\n\n"
        
        result_message += "请基于以上结果继续处理任务。"
        return result_message
    
    @abstractmethod
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """调用LLM进行Function Calling - 子类必须实现"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取智能体能力"""
        return self._capabilities
    
    @abstractmethod
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        pass
    
    @abstractmethod
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行增强任务"""
        pass
    
    # ==========================================================================
    # 🗂️ 文件操作方法
    # ==========================================================================
    
    async def autonomous_file_read(self, file_ref: FileReference) -> Optional[str]:
        """自主读取文件内容"""
        file_path = file_ref.file_path
        
        # 检查缓存
        if file_path in self.file_cache:
            self.logger.debug(f"📋 使用缓存文件: {file_path}")
            return self.file_cache[file_path]
        
        try:
            # 读取文件
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 缓存内容
                self.file_cache[file_path] = content
                self.file_metadata_cache[file_path] = {
                    "size": len(content),
                    "read_time": time.time()
                }
                
                self.logger.info(f"✅ 成功读取文件: {file_path} ({len(content)} bytes)")
                return content
            else:
                self.logger.warning(f"⚠️ 文件不存在: {file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 读取文件失败 {file_path}: {str(e)}")
            return None
    
    async def save_result_to_file(self, content: str, file_path: str, 
                                file_type: str = "unknown") -> FileReference:
        """保存结果到文件"""
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 清理内容：移除markdown格式标记
            cleaned_content = self._clean_file_content(content, file_type)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            # 创建文件引用
            file_ref = FileReference(
                file_path=file_path,
                file_type=file_type,
                description=f"{self.agent_id}生成的{file_type}文件",
                metadata={
                    "size": len(content),
                    "created_by": self.agent_id,
                    "creation_time": time.time()
                }
            )
            
            self.logger.info(f"💾 成功保存文件: {file_path}")
            return file_ref
            
        except Exception as e:
            self.logger.error(f"❌ 保存文件失败 {file_path}: {str(e)}")
            raise
    
    def _clean_file_content(self, content: str, file_type: str) -> str:
        """清理文件内容，移除不必要的格式标记"""
        cleaned_content = content.strip()
        
        # 对于代码文件，移除markdown代码块标记
        if file_type in ["verilog", "systemverilog", "python", "cpp", "c"]:
            lines = cleaned_content.split('\n')
            
            # 移除开头的```标记
            if lines and lines[0].strip().startswith('```'):
                lines = lines[1:]
                self.logger.debug(f"🧹 移除开头的markdown标记")
            
            # 移除结尾的```标记
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
                self.logger.debug(f"🧹 移除结尾的markdown标记")
            
            cleaned_content = '\n'.join(lines)
        
        # 移除多余的空行（保留文件结构）
        lines = cleaned_content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            if not (is_empty and prev_empty):  # 避免连续空行
                cleaned_lines.append(line)
            prev_empty = is_empty
        
        result = '\n'.join(cleaned_lines).strip()
        
        if result != content.strip():
            self.logger.info(f"🧹 内容已清理：{len(content)} -> {len(result)} 字符")
        
        return result
    
    # ==========================================================================
    # 🎯 任务处理方法
    # ==========================================================================
    
    async def process_task_with_file_references(self, task_message: TaskMessage) -> Dict[str, Any]:
        """处理带文件引用的任务消息"""
        self.logger.info(f"📨 收到任务消息: {task_message.message_type}")
        self.status = AgentStatus.WORKING
        
        try:
            # 1. 自主读取所有引用的文件
            file_contents = {}
            if task_message.file_references:
                self.logger.info(f"📁 开始读取 {len(task_message.file_references)} 个引用文件")
                
                for file_ref in task_message.file_references:
                    content = await self.autonomous_file_read(file_ref)
                    if content:
                        file_contents[file_ref.file_path] = {
                            "content": content,
                            "type": file_ref.file_type,
                            "description": file_ref.description
                        }
            
            # 2. 生成增强的prompt
            enhanced_prompt = self.create_file_enhanced_prompt(
                base_message=task_message.content,
                file_contents=file_contents
            )
            
            # 3. 执行任务处理
            result = await self.execute_enhanced_task(
                enhanced_prompt=enhanced_prompt,
                original_message=task_message,
                file_contents=file_contents
            )
            
            # 4. 记录任务历史
            self.task_history.append({
                "timestamp": time.time(),
                "task_id": task_message.task_id,
                "message_type": task_message.message_type,
                "result": result
            })
            
            self.status = AgentStatus.COMPLETED if result.get("success", False) else AgentStatus.FAILED
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 任务处理失败: {str(e)}")
            self.status = AgentStatus.FAILED
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    def create_file_enhanced_prompt(self, base_message: str, 
                                  file_contents: Dict[str, Dict]) -> str:
        """基于文件内容创建增强prompt"""
        if not file_contents:
            return base_message
        
        enhanced_prompt = f"{base_message}\n\n## 相关文件信息:\n"
        
        for file_path, content_info in file_contents.items():
            file_type = content_info.get("type", "unknown")
            description = content_info.get("description", "No description")
            content = content_info.get("content", "")
            
            enhanced_prompt += f"\n### {file_path} ({file_type})\n"
            enhanced_prompt += f"描述: {description}\n"
            enhanced_prompt += f"内容预览: {content[:500]}...\n"
        
        return enhanced_prompt
    
    # ==========================================================================
    # 🛠️ 工具调用方法
    # ==========================================================================
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """调用工具的便捷方法"""
        return await self.tool_registry.call_tool(
            name=tool_name,
            agent_id=self.agent_id,
            allowed_permissions=self.allowed_permissions,
            **kwargs
        )
    
    async def search_database_modules(self, module_name: str = "", description: str = "",
                                    limit: int = 10) -> Dict[str, Any]:
        """搜索数据库中的模块"""
        return await self.call_tool(
            "database_search_modules",
            module_name=module_name,
            description=description,
            limit=limit
        )
    
    async def get_database_module(self, module_id: int) -> Dict[str, Any]:
        """根据ID获取模块详情"""
        return await self.call_tool("database_get_module", module_id=module_id)
    
    async def search_by_functionality(self, functionality: str, tags: str = "",
                                    limit: int = 10) -> Dict[str, Any]:
        """按功能搜索模块"""
        return await self.call_tool(
            "database_search_by_functionality",
            functionality=functionality,
            tags=tags,
            limit=limit
        )
    
    async def get_similar_modules(self, bit_width: int, functionality: str,
                                limit: int = 5) -> Dict[str, Any]:
        """获取相似模块"""
        return await self.call_tool(
            "database_get_similar_modules",
            bit_width=bit_width,
            functionality=functionality,
            limit=limit
        )
    
    async def get_test_cases(self, module_id: int = None, module_name: str = "") -> Dict[str, Any]:
        """获取测试用例"""
        return await self.call_tool(
            "database_get_test_cases",
            module_id=module_id,
            module_name=module_name
        )
    
    async def search_design_patterns(self, pattern_type: str = "", description: str = "",
                                   limit: int = 10) -> Dict[str, Any]:
        """搜索设计模式"""
        return await self.call_tool(
            "database_search_design_patterns",
            pattern_type=pattern_type,
            description=description,
            limit=limit
        )
    
    async def get_database_schema(self) -> Dict[str, Any]:
        """获取数据库架构信息"""
        return await self.call_tool("database_get_schema")
    
    async def save_database_result_to_file(self, query_result: Dict[str, Any], 
                                         file_path: str, format_type: str = "json") -> Dict[str, Any]:
        """保存数据库查询结果到文件"""
        return await self.call_tool(
            "database_save_result_to_file",
            query_result=query_result,
            file_path=file_path,
            format_type=format_type
        )
    
    # ==========================================================================
    # 📝 标准化响应方法
    # ==========================================================================
    
    def create_response_builder(self, task_id: str) -> ResponseBuilder:
        """创建响应构建器"""
        return ResponseBuilder(
            agent_name=self.__class__.__name__,
            agent_id=self.agent_id,
            task_id=task_id
        )
    
    def create_success_response_formatted(self, task_id: str, message: str, 
                                        generated_files: List[str] = None, 
                                        format_type: ResponseFormat = ResponseFormat.JSON) -> str:
        """创建格式化的成功响应"""
        response = create_success_response(
            agent_name=self.__class__.__name__,
            agent_id=self.agent_id,
            task_id=task_id,
            message=message,
            generated_files=generated_files or []
        )
        return response.format_response(format_type)
    
    def create_error_response_formatted(self, task_id: str, error_message: str, 
                                      error_details: str = None,
                                      format_type: ResponseFormat = ResponseFormat.JSON) -> str:
        """创建格式化的错误响应"""
        response = create_error_response(
            agent_name=self.__class__.__name__,
            agent_id=self.agent_id,
            task_id=task_id,
            error_message=error_message,
            error_details=error_details
        )
        return response.format_response(format_type)
    
    def create_progress_response_formatted(self, task_id: str, message: str, 
                                         completion_percentage: float,
                                         next_steps: List[str] = None,
                                         format_type: ResponseFormat = ResponseFormat.JSON) -> str:
        """创建格式化的进度响应"""
        response = create_progress_response(
            agent_name=self.__class__.__name__,
            agent_id=self.agent_id,
            task_id=task_id,
            message=message,
            completion_percentage=completion_percentage,
            next_steps=next_steps or []
        )
        return response.format_response(format_type)
    
    async def create_advanced_response(self, task_id: str, response_type: ResponseType,
                                     status: TaskStatus, message: str, 
                                     completion_percentage: float,
                                     quality_metrics: QualityMetrics = None,
                                     format_type: ResponseFormat = ResponseFormat.JSON) -> str:
        """创建高级格式化响应"""
        builder = self.create_response_builder(task_id)
        
        # 检查是否有生成的文件需要添加
        recent_tasks = [task for task in self.task_history if task.get("task_id") == task_id]
        if recent_tasks:
            latest_task = recent_tasks[-1]
            result = latest_task.get("result", {})
            if "generated_files" in result:
                for file_path in result["generated_files"]:
                    file_type = self._detect_file_type(file_path)
                    builder.add_generated_file(file_path, file_type, f"Generated {file_type} file")
        
        # 添加下一步建议
        if status == TaskStatus.IN_PROGRESS:
            builder.add_next_step("继续任务执行")
        elif status == TaskStatus.SUCCESS:
            builder.add_next_step("任务已完成，等待下一步指令")
        elif status == TaskStatus.REQUIRES_RETRY:
            builder.add_next_step("需要重新执行任务")
        
        # 添加元数据
        builder.add_metadata("agent_class", self.__class__.__name__)
        builder.add_metadata("capabilities", [cap.value for cap in self._capabilities])
        builder.add_metadata("task_count", len(self.task_history))
        
        response = builder.build(
            response_type=response_type,
            status=status,
            message=message,
            completion_percentage=completion_percentage,
            quality_metrics=quality_metrics
        )
        
        return response.format_response(format_type)
    
    def _detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        if file_path.endswith('.v'):
            return 'verilog'
        elif file_path.endswith('_tb.v') or 'testbench' in file_path.lower():
            return 'testbench'
        elif file_path.endswith('.json'):
            return 'json'
        elif file_path.endswith('.md'):
            return 'documentation'
        elif file_path.endswith('.txt'):
            return 'text'
        else:
            return 'unknown'
    
    # ==========================================================================
    # 🔧 工具方法
    # ==========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self._capabilities],
            "task_count": len(self.task_history),
            "cache_size": len(self.file_cache)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.file_cache.clear()
        self.file_metadata_cache.clear()
        self.logger.info("🧹 缓存已清空")
    
    # ==========================================================================
    # 🔧 基础Function Calling工具实现
    # ==========================================================================
    
    async def _tool_write_file(self, filename: str, content: str, directory: str = None, **kwargs) -> Dict[str, Any]:
        """基础工具：写入文件"""
        try:
            self.logger.info(f"📝 写入文件: {filename}")
            
            # 如果没有指定目录，使用默认工件目录
            if directory is None:
                output_dir = self.default_artifacts_dir
            else:
                output_dir = Path(directory)
            
            # 确保目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建完整文件路径
            file_path = output_dir / filename
            
            # 清理内容（移除markdown标记等）
            cleaned_content = self._clean_file_content(content, self._detect_file_type(filename))
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            self.logger.info(f"✅ 文件写入成功: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "directory": str(output_dir),
                "content_length": len(cleaned_content),
                "message": f"成功写入文件: {file_path}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 文件写入失败: {str(e)}")
            return {
                "success": False,
                "error": f"文件写入异常: {str(e)}",
                "file_path": None
            }
    
    async def _tool_read_file(self, filepath: str, **kwargs) -> Dict[str, Any]:
        """基础工具：读取文件"""
        try:
            self.logger.info(f"📖 读取文件: {filepath}")
            
            file_path = Path(filepath)
            if not file_path.is_absolute():
                # 尝试相对路径
                file_path = Path("./output") / filepath
                if not file_path.exists():
                    file_path = Path(filepath)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"文件不存在: {filepath}",
                    "content": None
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"✅ 文件读取成功: {file_path} ({len(content)} 字符)")
            
            return {
                "success": True,
                "content": content,
                "file_path": str(file_path),
                "content_length": len(content),
                "message": f"成功读取文件: {file_path}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 文件读取失败: {str(e)}")
            return {
                "success": False,
                "error": f"文件读取异常: {str(e)}",
                "content": None
            }