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
        # 特殊处理不同智能体的日志映射
        if self.agent_id == "centralized_coordinator":
            self.logger = get_component_logger('coordinator', f"Agent.{self.agent_id}")
        elif self.agent_id == "real_verilog_design_agent":
            self.logger = get_component_logger('real_verilog_agent', f"Agent.{self.agent_id}")
        elif self.agent_id == "real_code_review_agent":
            self.logger = get_component_logger('real_code_reviewer', f"Agent.{self.agent_id}")
        else:
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
        
        tools_info += "### 🚨 错误处理与修复策略:\n"
        tools_info += "**当工具调用失败时，你应该：**\n"
        tools_info += "1. **仔细分析错误信息**: 详细阅读错误详情和建议修复方案\n"
        tools_info += "2. **识别错误类型**: 区分是文件错误、参数错误、权限错误还是语法错误\n"
        tools_info += "3. **针对性修复**: 基于错误类型采取对应的修复策略\n"
        tools_info += "4. **参数调整**: 根据失败分析调整工具调用参数\n"
        tools_info += "5. **逐步修复**: 优先修复关键阻塞性错误\n"
        tools_info += "6. **学习改进**: 避免在后续调用中重复相同错误\n\n"
        
        tools_info += "**常见错误修复指南：**\n"
        tools_info += "- **文件不存在**: 先创建文件或检查路径，使用绝对路径\n"
        tools_info += "- **权限错误**: 检查文件权限，确保目录可写\n"
        tools_info += "- **参数错误**: 验证所有必需参数，检查参数格式\n"
        tools_info += "- **语法错误**: 仔细检查代码语法，特别是括号和分号\n"
        tools_info += "- **网络错误**: 检查连接状态，考虑重试或使用备用方案\n\n"
        
        tools_info += "**智能重试策略：**\n"
        tools_info += "- 不要盲目重复相同的调用\n"
        tools_info += "- 基于错误分析调整参数再重试\n"
        tools_info += "- 如果多次失败，考虑替代方案\n"
        tools_info += "- 利用工具执行结果中的详细分析和建议\n\n"
        
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
    
    def _normalize_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """标准化工具参数，解决Schema不一致问题"""
        try:
            from core.schema_system.unified_schemas import UnifiedSchemas
            return UnifiedSchemas.resolve_parameter_aliases(parameters)
        except ImportError:
            # 如果统一Schema系统不可用，使用基本的别名映射
            normalized = parameters.copy()
            
            # 基本的参数别名映射
            alias_mappings = {
                "code": "verilog_code",
                "module_code": "verilog_code", 
                "design_code": "verilog_code",
                "name": "module_name",
                "module": "module_name",
                "path": "file_path",
                "filename": "file_path",
                "files": "verilog_files",
                "design_files": "verilog_files"
            }
            
            # 应用别名映射
            for alias, standard_name in alias_mappings.items():
                if alias in normalized and standard_name not in normalized:
                    normalized[standard_name] = normalized[alias]
                    self.logger.debug(f"🔄 参数别名映射: {alias} -> {standard_name}")
            
            return normalized
        except Exception as e:
            self.logger.debug(f"参数标准化失败: {e}")
            return parameters
    
    async def _execute_tool_call_with_retry(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用，支持失败重试和LLM反馈"""
        last_error = None
        
        for attempt in range(self.max_tool_retry_attempts):
            try:
                self.logger.info(f"🔧 执行工具调用: {tool_call.tool_name} (尝试 {attempt + 1}/{self.max_tool_retry_attempts})")
                
                # 标准化参数（解决Schema不一致问题）
                normalized_parameters = self._normalize_tool_parameters(tool_call.tool_name, tool_call.parameters)
                if normalized_parameters != tool_call.parameters:
                    self.logger.info(f"🎯 {tool_call.tool_name} 参数已标准化")
                    # 使用标准化后的参数创建新的工具调用
                    tool_call = ToolCall(
                        tool_name=tool_call.tool_name,
                        parameters=normalized_parameters,
                        call_id=tool_call.call_id
                    )
                
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
                
                # 检查工具内部是否报告失败
                tool_success = True
                tool_error = None
                
                if isinstance(result, dict):
                    tool_success = result.get('success', True)
                    tool_error = result.get('error', None)
                    
                    # 如果工具内部报告失败，记录并抛出异常以触发重试
                    if not tool_success:
                        error_msg = tool_error or "工具内部执行失败"
                        self.logger.warning(f"⚠️ 工具内部报告失败 {tool_call.tool_name}: {error_msg}")
                        raise Exception(error_msg)
                
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
        """格式化工具执行结果 - 增强版，为LLM提供丰富的上下文信息"""
        result_message = "## 🔧 工具执行结果详细报告\n\n"
        
        # 统计信息
        total_calls = len(tool_calls)
        successful_calls = sum(1 for tr in tool_results if tr.success)
        failed_calls = total_calls - successful_calls
        
        result_message += f"📊 **执行摘要**: {successful_calls}/{total_calls} 个工具成功执行"
        if failed_calls > 0:
            result_message += f" ({failed_calls} 个失败)"
        result_message += "\n\n"
        
        # 详细结果
        for i, (tool_call, tool_result) in enumerate(zip(tool_calls, tool_results), 1):
            if tool_result.success:
                result_message += f"### ✅ 工具 {i}: {tool_call.tool_name} - 执行成功\n"
                result_message += f"**调用参数**: {self._format_parameters(tool_call.parameters)}\n"
                formatted_result = self._format_tool_result(tool_result.result)
                result_message += f"**执行结果**: {formatted_result}\n"
                
                # 检查是否有错误修复建议（即使工具执行成功）
                if isinstance(tool_result.result, dict):
                    if tool_result.result.get('needs_fix') and tool_result.result.get('fix_suggestion'):
                        result_message += f"🔧 **智能修复建议**: {tool_result.result['fix_suggestion']}\n"
                        result_message += f"**下一步行动**: 建议根据修复建议调用write_file工具修改代码，然后重新测试\n\n"
                    else:
                        result_message += f"**状态**: 成功完成，可进行下一步操作\n\n"
                else:
                    result_message += f"**状态**: 成功完成，可进行下一步操作\n\n"
            else:
                result_message += f"### ❌ 工具 {i}: {tool_call.tool_name} - 执行失败\n"
                result_message += f"**调用参数**: {self._format_parameters(tool_call.parameters)}\n"
                result_message += f"**错误信息**: {tool_result.error}\n"
                
                # 如果有详细的错误上下文，显示它
                if hasattr(tool_result, 'context') and tool_result.context:
                    failure_contexts = tool_result.context.get('failure_chain', [])
                    if failure_contexts:
                        latest_context = failure_contexts[-1]
                        if 'detailed_error' in latest_context:
                            result_message += f"**详细分析**:\n```\n{latest_context['detailed_error']}\n```\n"
                
                result_message += f"**影响**: 此工具调用失败可能影响后续操作的执行\n"
                result_message += f"**建议**: 请根据错误信息分析问题并调整参数重新调用\n\n"
        
        # 失败分析和建议
        if failed_calls > 0:
            result_message += "## 🚨 失败分析与修复建议\n\n"
            
            # 分析失败模式
            failure_patterns = self._analyze_failure_patterns(tool_calls, tool_results)
            if failure_patterns:
                result_message += "### 📈 失败模式分析\n"
                for pattern, description in failure_patterns.items():
                    result_message += f"- **{pattern}**: {description}\n"
                result_message += "\n"
            
            # 智能修复建议
            result_message += "### 💡 智能修复建议\n"
            repair_suggestions = self._generate_repair_suggestions(tool_calls, tool_results)
            for i, suggestion in enumerate(repair_suggestions, 1):
                result_message += f"{i}. {suggestion}\n"
            result_message += "\n"
            
            # 替代方案
            alternatives = self._suggest_alternatives(tool_calls, tool_results)
            if alternatives:
                result_message += "### 🔄 替代方案\n"
                for alt in alternatives:
                    result_message += f"- {alt}\n"
                result_message += "\n"
        
        # 下一步行动指导
        result_message += "## 🎯 下一步行动指导\n\n"
        if failed_calls == 0:
            result_message += "✅ 所有工具执行成功！请基于执行结果继续完成任务。\n"
            result_message += "- 检查输出结果是否符合预期\n"
            result_message += "- 根据结果进行下一步操作\n"
            result_message += "- 如需进一步处理，请继续调用相应工具\n"
        else:
            result_message += "⚠️ 存在失败的工具调用，建议采取以下行动：\n"
            result_message += "1. **优先修复关键失败**: 专注解决阻塞性错误\n"
            result_message += "2. **调整参数重试**: 基于错误分析修改调用参数\n"
            result_message += "3. **考虑替代方案**: 如果直接修复困难，尝试其他方法\n"
            result_message += "4. **寻求帮助**: 如果问题持续，请描述遇到的具体问题\n"
        
        result_message += "\n💭 **重要提示**: 请仔细分析上述结果，基于具体的成功/失败情况做出明智的下一步决策。"
        
        return result_message
    
    def _format_parameters(self, parameters: Dict[str, Any]) -> str:
        """格式化参数显示"""
        if not parameters:
            return "无参数"
        
        formatted_params = []
        for key, value in parameters.items():
            if isinstance(value, str) and len(value) > 100:
                # 长字符串截断显示
                formatted_params.append(f"{key}: '{value[:50]}...'[截断，总长度:{len(value)}]")
            elif isinstance(value, (list, dict)) and len(str(value)) > 200:
                # 复杂对象简化显示
                formatted_params.append(f"{key}: {type(value).__name__}[长度:{len(value)}]")
            else:
                formatted_params.append(f"{key}: {repr(value)}")
        
        return "{ " + ", ".join(formatted_params) + " }"
    
    def _format_tool_result(self, result: Any) -> str:
        """格式化工具结果显示"""
        if result is None:
            return "无返回值"
        elif isinstance(result, dict):
            # 字典结果格式化
            if 'success' in result:
                status = "✅ 成功" if result.get('success') else "❌ 失败"
                details = []
                for key, value in result.items():
                    if key != 'success':
                        if isinstance(value, str) and len(value) > 100:
                            details.append(f"{key}: '{value[:50]}...'[截断]")
                        else:
                            details.append(f"{key}: {value}")
                return f"{status}; {'; '.join(details)}"
            else:
                return str(result)
        elif isinstance(result, str) and len(result) > 200:
            return f"'{result[:100]}...'[内容截断，总长度:{len(result)}字符]"
        else:
            return str(result)
    
    def _analyze_failure_patterns(self, tool_calls: List[ToolCall], tool_results: List[ToolResult]) -> Dict[str, str]:
        """分析失败模式"""
        patterns = {}
        
        failed_tools = [(tc, tr) for tc, tr in zip(tool_calls, tool_results) if not tr.success]
        if not failed_tools:
            return patterns
        
        # 分析文件相关失败
        file_failures = [tc for tc, tr in failed_tools if 'file' in tc.tool_name.lower()]
        if file_failures:
            patterns["文件操作失败"] = f"共{len(file_failures)}个文件操作工具失败，可能是路径或权限问题"
        
        # 分析网络相关失败
        network_failures = [tc for tc, tr in failed_tools if any(keyword in tr.error.lower() 
                           for keyword in ['connection', 'timeout', 'network', 'api'])]
        if network_failures:
            patterns["网络连接问题"] = f"检测到{len(network_failures)}个网络相关错误，可能需要检查连接状态"
        
        # 分析参数相关失败
        param_failures = [tc for tc, tr in failed_tools if any(keyword in tr.error.lower() 
                         for keyword in ['parameter', 'argument', 'missing', 'required'])]
        if param_failures:
            patterns["参数问题"] = f"发现{len(param_failures)}个参数相关错误，需要检查调用参数"
        
        # 分析权限相关失败
        permission_failures = [tc for tc, tr in failed_tools if 'permission' in tr.error.lower()]
        if permission_failures:
            patterns["权限问题"] = f"存在{len(permission_failures)}个权限相关错误，需要检查访问权限"
        
        return patterns
    
    def _generate_repair_suggestions(self, tool_calls: List[ToolCall], tool_results: List[ToolResult]) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        failed_pairs = [(tc, tr) for tc, tr in zip(tool_calls, tool_results) if not tr.success]
        
        for tool_call, tool_result in failed_pairs:
            error_lower = tool_result.error.lower()
            
            if 'file not found' in error_lower or 'no such file' in error_lower:
                suggestions.append(f"对于工具 {tool_call.tool_name}: 检查文件路径，确保文件存在或先创建文件")
            elif 'permission denied' in error_lower:
                suggestions.append(f"对于工具 {tool_call.tool_name}: 检查文件/目录权限，必要时修改权限设置")
            elif 'parameter' in error_lower or 'argument' in error_lower:
                suggestions.append(f"对于工具 {tool_call.tool_name}: 检查参数格式和必需参数是否完整")
            elif 'syntax' in error_lower:
                suggestions.append(f"对于工具 {tool_call.tool_name}: 检查输入代码的语法正确性")
            else:
                suggestions.append(f"对于工具 {tool_call.tool_name}: 分析具体错误信息 '{tool_result.error[:50]}...' 并相应调整")
        
        # 通用建议
        if len(failed_pairs) > 1:
            suggestions.append("检查是否存在工具间的依赖关系，考虑调整执行顺序")
        
        return suggestions[:5]  # 限制建议数量
    
    def _suggest_alternatives(self, tool_calls: List[ToolCall], tool_results: List[ToolResult]) -> List[str]:
        """建议替代方案"""
        alternatives = []
        
        failed_tools = [tc.tool_name for tc, tr in zip(tool_calls, tool_results) if not tr.success]
        
        if 'write_file' in failed_tools:
            alternatives.append("考虑使用不同的文件路径或目录")
            alternatives.append("检查磁盘空间是否充足")
        
        if 'read_file' in failed_tools:
            alternatives.append("尝试使用绝对路径而非相对路径")
            alternatives.append("确认目标文件确实已创建")
        
        if any('simulation' in tool for tool in failed_tools):
            alternatives.append("检查Verilog代码语法，考虑使用在线语法检查器")
            alternatives.append("确认仿真工具(如iverilog)已正确安装")
        
        return alternatives[:3]  # 限制数量
    
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
        """基础工具：写入文件（增强版，支持中央文件管理）"""
        try:
            self.logger.info(f"📝 写入文件: {filename}")
            
            # 尝试使用实验管理器 + 中央文件管理器
            try:
                # 先尝试实验管理器
                try:
                    from core.experiment_manager import get_experiment_manager
                    exp_manager = get_experiment_manager()
                    
                    if exp_manager.current_experiment_path:
                        # 清理内容
                        cleaned_content = self._clean_file_content(content, self._detect_file_type(filename))
                        file_type = self._determine_file_type(filename, cleaned_content)
                        
                        # 确定子文件夹
                        if "testbench" in filename.lower() or "_tb" in filename.lower():
                            subdir = "testbenches"
                        elif filename.endswith('.v'):
                            subdir = "designs"
                        else:
                            subdir = "artifacts"
                        
                        # 保存到实验文件夹
                        exp_file_path = exp_manager.save_file(
                            content=cleaned_content,
                            filename=filename,
                            subdir=subdir,
                            description=f"由{self.agent_id}创建的{file_type}文件"
                        )
                        
                        if exp_file_path:
                            # 同时注册到中央文件管理器
                            try:
                                from core.file_manager import get_file_manager
                                file_manager = get_file_manager()
                                file_ref = file_manager.save_file(
                                    content=cleaned_content,
                                    filename=filename,
                                    file_type=file_type,
                                    created_by=self.agent_id,
                                    description=f"由{self.agent_id}创建的{file_type}文件",
                                    file_path=str(exp_file_path)
                                )
                                
                                self.logger.info(f"✅ 文件已保存到实验文件夹: {filename} (ID: {file_ref.file_id})")
                                
                                return {
                                    "success": True,
                                    "message": f"文件 {filename} 已成功保存到实验文件夹",
                                    "file_path": str(exp_file_path),
                                    "file_id": file_ref.file_id,
                                    "file_type": file_ref.file_type,
                                    "filename": filename,
                                    "content_length": len(cleaned_content),
                                    "experiment_path": str(exp_manager.current_experiment_path),
                                    "subdir": subdir,
                                    "file_reference": {
                                        "file_id": file_ref.file_id,
                                        "file_path": str(exp_file_path),
                                        "file_type": file_ref.file_type,
                                        "created_by": file_ref.created_by,
                                        "created_at": file_ref.created_at,
                                        "description": file_ref.description
                                    }
                                }
                            except Exception as e:
                                self.logger.warning(f"⚠️ 中央文件管理器注册失败: {e}")
                                # 即使中央管理器失败，文件已经保存到实验文件夹
                                return {
                                    "success": True,
                                    "message": f"文件 {filename} 已成功保存到实验文件夹",
                                    "file_path": str(exp_file_path),
                                    "file_id": None,
                                    "file_type": file_type,
                                    "filename": filename,
                                    "content_length": len(cleaned_content),
                                    "experiment_path": str(exp_manager.current_experiment_path),
                                    "subdir": subdir
                                }
                except ImportError:
                    self.logger.debug("实验管理器不可用")
                except Exception as e:
                    self.logger.warning(f"实验管理器保存失败: {e}")
                
                # 回退到纯中央文件管理器
                from core.file_manager import get_file_manager
                file_manager = get_file_manager()
                
                # 清理内容（移除markdown标记等）
                cleaned_content = self._clean_file_content(content, self._detect_file_type(filename))
                
                # 确定文件类型
                file_type = self._determine_file_type(filename, cleaned_content)
                
                # 使用中央文件管理器保存文件
                file_ref = file_manager.save_file(
                    content=cleaned_content,
                    filename=filename,
                    file_type=file_type,
                    created_by=self.agent_id,
                    description=f"由{self.agent_id}创建的{file_type}文件"
                )
                
                self.logger.info(f"✅ 文件已通过中央管理器保存: {filename} (ID: {file_ref.file_id})")
                
                return {
                    "success": True,
                    "message": f"文件 {filename} 已成功保存到中央管理器",
                    "file_path": file_ref.file_path,
                    "file_id": file_ref.file_id,
                    "file_type": file_ref.file_type,
                    "filename": filename,
                    "content_length": len(cleaned_content),
                    "file_reference": {
                        "file_id": file_ref.file_id,
                        "file_path": file_ref.file_path,
                        "file_type": file_ref.file_type,
                        "created_by": file_ref.created_by,
                        "created_at": file_ref.created_at,
                        "description": file_ref.description
                    }
                }
            except ImportError:
                self.logger.warning("中央文件管理器不可用，使用传统文件保存方法")
            except Exception as e:
                self.logger.warning(f"中央文件管理器保存失败: {e}，回退到传统方法")
            
            # 传统文件保存方法（保持向后兼容性）
            # 如果没有指定目录，使用默认工件目录
            if directory is None:
                output_dir = self.default_artifacts_dir
            else:
                output_dir = Path(directory)
            
            # 确保目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建完整文件路径 - 处理可能的路径重复问题
            # 如果filename已经包含路径信息，只取文件名部分
            if '/' in filename or '\\' in filename:
                filename = Path(filename).name
                self.logger.info(f"🔧 提取文件名: {filename}")
            
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
    
    def _determine_file_type(self, filename: str, content: str) -> str:
        """根据文件名和内容确定文件类型"""
        filename_lower = filename.lower()
        
        # 根据文件扩展名判断
        if filename_lower.endswith('.v'):
            # 进一步判断是设计文件还是测试台
            if 'testbench' in filename_lower or '_tb' in filename_lower or 'tb_' in filename_lower:
                return "testbench"
            elif 'module' in content and ('initial' in content or '$monitor' in content or '$display' in content):
                return "testbench"
            else:
                return "verilog"
        elif filename_lower.endswith('.sv'):
            return "verilog"
        elif filename_lower.endswith(('.txt', '.log')):
            return "report"
        elif filename_lower.endswith('.json'):
            return "analysis"
        else:
            return "temp"
    
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
    
    # ==========================================================================
    # 🚨 错误处理增强方法 - 修复缺失的关键功能
    # ==========================================================================
    
    async def _enhance_error_with_context(self, failure_context: Dict[str, Any]) -> str:
        """增强错误信息，基于上下文生成详细分析"""
        try:
            tool_name = failure_context.get("tool_name", "unknown")
            error = failure_context.get("error", "unknown error")
            error_type = failure_context.get("error_type", "Exception")
            parameters = failure_context.get("parameters", {})
            attempt = failure_context.get("attempt", 1)
            
            # 分析错误类型和常见原因
            error_analysis = self._analyze_error_type(error, error_type, tool_name, parameters)
            
            # 构建增强的错误描述
            enhanced_error = f"""
=== 工具执行失败详细分析 ===
🔧 工具名称: {tool_name}
📝 错误类型: {error_type}
🔍 原始错误: {error}
📊 尝试次数: {attempt}/{self.max_tool_retry_attempts}
⚙️ 调用参数: {parameters}

🎯 错误分析:
{error_analysis['category']}: {error_analysis['description']}

💡 可能原因:
{chr(10).join(f"• {cause}" for cause in error_analysis['possible_causes'])}

🔧 建议修复:
{chr(10).join(f"• {fix}" for fix in error_analysis['suggested_fixes'])}

⚠️ 影响评估: {error_analysis['impact']}
""".strip()
            
            return enhanced_error
            
        except Exception as e:
            self.logger.warning(f"⚠️ 错误增强失败: {str(e)}")
            return f"工具 {failure_context.get('tool_name', 'unknown')} 执行失败: {failure_context.get('error', 'unknown')}"
    
    def _analyze_error_type(self, error: str, error_type: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """分析错误类型并提供详细信息"""
        error_lower = error.lower()
        
        # 文件相关错误
        if "no such file or directory" in error_lower or "filenotfounderror" in error_type.lower():
            return {
                "category": "文件访问错误",
                "description": "指定的文件或目录不存在",
                "possible_causes": [
                    "文件路径不正确或文件未创建",
                    "相对路径解析错误",
                    "文件被删除或移动",
                    "权限不足无法访问文件"
                ],
                "suggested_fixes": [
                    "检查文件路径是否正确",
                    "使用绝对路径替代相对路径",
                    "先创建文件或目录再访问",
                    "检查文件权限设置"
                ],
                "impact": "中等 - 可通过修正路径或创建文件解决"
            }
        
        # 权限相关错误
        elif "permission denied" in error_lower or "permissionerror" in error_type.lower():
            return {
                "category": "权限访问错误", 
                "description": "没有足够权限执行操作",
                "possible_causes": [
                    "文件或目录权限设置不当",
                    "用户权限不足",
                    "文件被其他进程占用",
                    "目录为只读状态"
                ],
                "suggested_fixes": [
                    "检查并修改文件权限",
                    "使用具有足够权限的用户运行",
                    "确保文件未被其他进程占用",
                    "检查目录写入权限"
                ],
                "impact": "中等 - 需要调整权限设置"
            }
        
        # 参数相关错误
        elif "typeerror" in error_type.lower() or "missing" in error_lower or "required" in error_lower:
            return {
                "category": "参数错误",
                "description": "工具调用参数不正确或缺失",
                "possible_causes": [
                    "必需参数未提供",
                    "参数类型不匹配",
                    "参数值格式错误",
                    "参数名称拼写错误"
                ],
                "suggested_fixes": [
                    "检查所有必需参数是否提供",
                    "验证参数类型和格式",
                    "参考工具文档确认参数要求",
                    "使用正确的参数名称"
                ],
                "impact": "低 - 通过修正参数即可解决"
            }
        
        # 编程语言特定错误（Verilog等）
        elif "syntax error" in error_lower or "parse error" in error_lower:
            return {
                "category": "语法错误",
                "description": "代码存在语法错误",
                "possible_causes": [
                    "Verilog语法不正确",
                    "缺少分号或括号不匹配",
                    "关键字拼写错误",
                    "模块定义不完整"
                ],
                "suggested_fixes": [
                    "检查代码语法规范",
                    "验证括号和分号匹配",
                    "确认关键字拼写正确",
                    "补全模块定义"
                ],
                "impact": "中等 - 需要修复代码语法"
            }
        
        # 网络/连接相关错误
        elif "connection" in error_lower or "timeout" in error_lower:
            return {
                "category": "连接错误",
                "description": "网络连接或服务连接失败",
                "possible_causes": [
                    "网络连接不稳定",
                    "服务器响应超时",
                    "API密钥或认证失败",
                    "服务暂时不可用"
                ],
                "suggested_fixes": [
                    "检查网络连接状态",
                    "增加连接超时时间",
                    "验证API密钥和认证信息",
                    "稍后重试或使用备用服务"
                ],
                "impact": "高 - 影响外部服务调用"
            }
        
        # 内存/资源相关错误
        elif "memory" in error_lower or "resource" in error_lower:
            return {
                "category": "资源不足错误",
                "description": "系统资源不足",
                "possible_causes": [
                    "内存不足",
                    "磁盘空间不够",
                    "文件句柄耗尽",
                    "CPU资源紧张"
                ],
                "suggested_fixes": [
                    "释放不必要的内存",
                    "清理磁盘空间",
                    "关闭不用的文件句柄",
                    "优化资源使用"
                ],
                "impact": "高 - 需要释放系统资源"
            }
        
        # 通用错误
        else:
            return {
                "category": "通用执行错误",
                "description": f"工具执行过程中发生异常: {error_type}",
                "possible_causes": [
                    "工具内部逻辑错误",
                    "输入数据格式问题",
                    "环境配置不当",
                    "依赖库版本冲突"
                ],
                "suggested_fixes": [
                    "检查工具输入数据",
                    "验证环境配置",
                    "更新或重装依赖库",
                    "查看详细错误日志"
                ],
                "impact": "中等 - 需要具体分析解决"
            }
    
    async def _get_llm_retry_advice(self, failure_context: Dict[str, Any]) -> str:
        """使用LLM分析错误并提供重试建议"""
        try:
            # 获取详细的错误信息
            enhanced_error = failure_context.get("detailed_error", "")
            tool_name = failure_context.get("tool_name", "unknown")
            parameters = failure_context.get("parameters", {})
            attempt = failure_context.get("attempt", 1)
            
            # 构建LLM分析prompt
            analysis_prompt = f"""
作为一位经验丰富的系统调试专家，请分析以下工具执行失败的情况并提供具体的修复建议。

## 失败详情
{enhanced_error}

## 历史失败记录
{json.dumps([ctx for ctx in self.tool_failure_contexts[-3:]], indent=2, ensure_ascii=False, default=str)}

## 请提供以下建议：

### 1. 根本原因分析
- 这个错误的最可能根本原因是什么？
- 为什么之前的尝试失败了？

### 2. 具体修复步骤
- 应该如何修改参数？
- 需要什么前置条件？
- 有什么替代方案？

### 3. 重试策略
- 是否值得重试？
- 如果重试，应该如何调整？
- 预期成功概率？

请简洁明确地回答，重点关注可操作的建议。
"""
            
            # 如果有LLM客户端，使用LLM分析
            if hasattr(self, 'llm_client') and self.llm_client:
                try:
                    advice = await self.llm_client.send_prompt(
                        prompt=analysis_prompt,
                        temperature=0.3,
                        max_tokens=3000,
                        system_prompt="你是一位专业的系统调试和错误分析专家，专注于提供准确、可操作的技术建议。"
                    )
                    return advice.strip()
                except Exception as llm_error:
                    self.logger.warning(f"⚠️ LLM分析失败: {str(llm_error)}")
            
            # 备用方案：基于规则的建议
            return self._generate_rule_based_advice(failure_context)
            
        except Exception as e:
            self.logger.warning(f"⚠️ 重试建议生成失败: {str(e)}")
            return "建议检查错误详情并调整参数后重试"
    
    def _generate_rule_based_advice(self, failure_context: Dict[str, Any]) -> str:
        """生成基于规则的重试建议（备用方案）"""
        tool_name = failure_context.get("tool_name", "")
        error = failure_context.get("error", "").lower()
        attempt = failure_context.get("attempt", 1)
        
        advice_parts = []
        
        # 基于工具类型的建议
        if "write_file" in tool_name:
            advice_parts.append("• 检查目录是否存在，文件路径是否正确")
            advice_parts.append("• 确保有写入权限")
        elif "read_file" in tool_name:
            advice_parts.append("• 确认文件确实存在")
            advice_parts.append("• 尝试使用绝对路径")
        elif "simulation" in tool_name or "iverilog" in tool_name:
            advice_parts.append("• 检查Verilog代码语法")
            advice_parts.append("• 确保iverilog已正确安装")
        
        # 基于错误类型的建议
        if "not found" in error:
            advice_parts.append("• 检查文件或命令是否存在")
            advice_parts.append("• 验证路径和环境变量")
        elif "permission" in error:
            advice_parts.append("• 检查文件和目录权限")
            advice_parts.append("• 确保运行用户有足够权限")
        elif "syntax" in error:
            advice_parts.append("• 仔细检查代码语法")
            advice_parts.append("• 使用代码格式化工具")
        
        # 基于尝试次数的建议
        if attempt >= 2:
            advice_parts.append("• 考虑使用不同的参数或方法")
            advice_parts.append("• 检查是否需要更换工具或策略")
        
        if not advice_parts:
            advice_parts.append("• 检查错误详情，调整参数后重试")
            advice_parts.append("• 如果问题持续，考虑使用替代方案")
        
        return f"基于错误分析的重试建议：\n" + "\n".join(advice_parts)