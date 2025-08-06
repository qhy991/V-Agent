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
        
        # 🧠 对话上下文管理 - 新增
        self.conversation_history: List[Dict[str, str]] = []
        self.current_conversation_id: Optional[str] = None
        self.conversation_start_time: Optional[float] = None
        self._last_conversation_id: Optional[str] = None  # 🔧 新增：记录上一次对话ID，用于智能体独立上下文管理
        
        # 🔧 任务上下文支持 - 用于协调器集成
        self.current_task_context: Optional[Any] = None  # TaskContext实例
        
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
                "filename": {"type": "string", "description": "文件名", "required": False},
                "file_path": {"type": "string", "description": "文件路径（filename的别名）", "required": False},
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
    
    def set_task_context(self, task_context):
        """设置任务上下文，用于协调器集成
        
        Args:
            task_context: TaskContext实例，包含对话历史管理功能
        """
        self.current_task_context = task_context
        if task_context:
            self.logger.info(f"🔗 设置任务上下文: {task_context.task_id}")
        else:
            self.logger.info("🔗 清除任务上下文")
    
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
    
    async def process_with_function_calling(self, user_request: str, max_iterations: int = 10, 
                                          conversation_id: str = None, preserve_context: bool = True,
                                          enable_self_continuation: bool = True, max_self_iterations: int = 3) -> str:
        """使用Function Calling处理用户请求
        
        Args:
            user_request: 用户请求
            max_iterations: 最大工具调用迭代次数
            conversation_id: 对话ID
            preserve_context: 是否保持对话上下文
            enable_self_continuation: 是否启用自主任务继续
            max_self_iterations: 自主继续的最大次数
        """
        self.logger.info(f"🚀 开始Function Calling处理: {user_request[:100]}...")
        self.logger.info(f"🔄 自主继续模式: {'启用' if enable_self_continuation else '禁用'}")
        
        # 🧠 上下文管理日志
        if conversation_id:
            # 🔧 修复：为每个智能体创建独立的对话ID，避免对话历史混淆
            agent_specific_conversation_id = f"{self.agent_id}_{conversation_id}"
            self.current_conversation_id = agent_specific_conversation_id
            if self.conversation_start_time is None:
                self.conversation_start_time = time.time()
            self.logger.info(f"🔗 智能体独立对话ID: {agent_specific_conversation_id} (原始ID: {conversation_id})")
        else:
            # 生成新的对话ID
            self.current_conversation_id = f"{self.agent_id}_{int(time.time())}"
            self.conversation_start_time = time.time()
            self.logger.info(f"🆕 生成新对话ID: {self.current_conversation_id}")
        
        # 🔧 修复：决定是否保留对话历史 - 基于智能体特定的对话ID
        if preserve_context and self.conversation_history:
            # 检查当前对话历史是否属于同一个智能体对话
            current_conversation_id = getattr(self, 'current_conversation_id', None)
            if current_conversation_id and hasattr(self, '_last_conversation_id') and self._last_conversation_id == current_conversation_id:
                self.logger.info(f"📚 保留现有对话历史: {len(self.conversation_history)} 条消息")
                conversation = self.conversation_history.copy()
                # 添加新的用户消息
                conversation.append({"role": "user", "content": user_request})
            else:
                # 🔧 修复：不同智能体或不同对话，创建新的对话历史
                self.logger.info(f"🆕 创建新的对话历史（智能体独立上下文）")
                conversation = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_request}
                ]
                # 重置对话历史
                self.conversation_history = conversation.copy()
                self.conversation_start_time = time.time()
                # 记录当前对话ID
                self._last_conversation_id = current_conversation_id
        else:
            self.logger.info(f"🆕 创建新的对话历史")
            # 构建新的对话历史
            conversation = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_request}
            ]
            # 重置对话历史
            self.conversation_history = conversation.copy()
            self.conversation_start_time = time.time()
            # 记录当前对话ID
            self._last_conversation_id = getattr(self, 'current_conversation_id', None)
        
        # 记录对话统计信息
        self.logger.info(f"📊 对话统计: 总消息数={len(conversation)}, 对话时长={time.time() - (self.conversation_start_time or time.time()):.1f}秒")
        
        # 🔧 TaskContext对话记录 - 记录用户请求
        if self.current_task_context and hasattr(self.current_task_context, 'add_conversation_message'):
            self.current_task_context.add_conversation_message(
                role="user",
                content=user_request,
                agent_id=self.agent_id
            )
        
        # 🎯 执行初始任务
        initial_result = await self._execute_single_task_cycle(conversation, user_request, max_iterations)
        
        # 🔄 如果启用自主继续，则进行自我评估和任务继续
        if enable_self_continuation:
            final_result = await self._execute_self_continuation(conversation, initial_result, user_request, max_self_iterations, max_iterations)
        else:
            final_result = initial_result
        
        # 🔧 TaskContext对话记录 - 记录智能体响应
        if self.current_task_context and hasattr(self.current_task_context, 'add_conversation_message'):
            self.current_task_context.add_conversation_message(
                role="assistant",
                content=final_result,
                agent_id=self.agent_id
            )
        
        return final_result
    
    async def process_with_optimized_function_calling(self, user_request: str, max_iterations: int = 10,
                                                    conversation_id: str = None, preserve_context: bool = True,
                                                    enable_self_continuation: bool = True, max_self_iterations: int = 3) -> str:
        """使用优化的Function Calling处理用户请求（支持智能缓存和上下文管理）"""
        self.logger.info(f"🚀 开始优化Function Calling处理: {user_request[:100]}...")
        self.logger.info(f"🔄 自主继续模式: {'启用' if enable_self_continuation else '禁用'}")
        
        # 🧠 上下文管理日志
        if conversation_id:
            self.current_conversation_id = conversation_id
            if self.conversation_start_time is None:
                self.conversation_start_time = time.time()
            self.logger.info(f"🔗 对话ID: {conversation_id}")
        else:
            # 生成新的对话ID
            self.current_conversation_id = f"{self.agent_id}_{int(time.time())}"
            self.conversation_start_time = time.time()
            self.logger.info(f"🆕 生成新对话ID: {self.current_conversation_id}")
        
        # 🎯 执行优化的任务周期
        initial_result = await self._execute_optimized_task_cycle(user_request, max_iterations)
        
        # 🔄 如果启用自主继续，则进行自我评估和任务继续
        if enable_self_continuation:
            return await self._execute_optimized_self_continuation(initial_result, user_request, max_self_iterations, max_iterations)
        else:
            return initial_result
    
    async def _execute_optimized_task_cycle(self, user_request: str, max_iterations: int) -> str:
        """执行优化的任务周期（使用智能缓存和上下文管理）"""
        
        for iteration in range(max_iterations):
            self.logger.info(f"🔄 优化Function Calling 迭代 {iteration + 1}/{max_iterations}")
            
            try:
                # 使用优化的LLM调用
                llm_response = await self._call_llm_optimized(user_request, iteration == 0)
                
                # 解析工具调用
                tool_calls = self._parse_tool_calls_from_response(llm_response)
                
                if not tool_calls:
                    # 没有工具调用，返回最终结果
                    self.logger.info(f"✅ 任务完成，无需调用工具")
                    return llm_response
                
                # 执行工具调用
                all_tool_results = []
                for tool_call in tool_calls:
                    result = await self._execute_tool_call_with_retry(tool_call)
                    all_tool_results.append(result)
                
                # 构建工具结果消息
                result_message = self._format_tool_results(tool_calls, all_tool_results)
                
                # 更新用户请求为工具结果，用于下一次迭代
                user_request = result_message
                
            except Exception as e:
                self.logger.error(f"❌ 优化Function Calling迭代失败: {str(e)}")
                return f"处理请求时发生错误: {str(e)}"
        
        # 达到最大迭代次数，获取最终响应
        try:
            final_response = await self._call_llm_optimized(user_request, False)
            return final_response
        except Exception as e:
            self.logger.error(f"❌ 最终响应生成失败: {str(e)}")
            return f"生成最终响应时发生错误: {str(e)}"
    
    async def _call_llm_optimized(self, user_message: str, is_first_call: bool = False) -> str:
        """优化的LLM调用方法"""
        try:
            # 获取system prompt
            system_prompt = self.system_prompt
            
            # 调用优化的LLM客户端
            response = await self.llm_client.send_prompt_optimized(
                conversation_id=self.current_conversation_id,
                user_message=user_message,
                system_prompt=system_prompt if is_first_call else None,  # 只在第一次调用时传递system prompt
                temperature=0.3,
                max_tokens=4000,
                force_refresh_system=is_first_call
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ 优化LLM调用失败: {str(e)}")
            raise
    
    async def _execute_optimized_self_continuation(self, initial_result: str, original_request: str, 
                                                 max_self_iterations: int, max_iterations: int) -> str:
        """优化的自主任务继续"""
        self.logger.info(f"🧠 开始优化的自主任务继续，最大迭代次数: {max_self_iterations}")
        
        current_result = initial_result
        
        for self_iteration in range(max_self_iterations):
            self.logger.info(f"🧠 自主继续迭代 {self_iteration + 1}/{max_self_iterations}")
            
            try:
                # 构建自我评估提示
                evaluation_prompt = self._build_self_evaluation_prompt(original_request, current_result)
                
                # 使用优化的LLM调用进行自我评估
                evaluation_response = await self._call_llm_optimized(evaluation_prompt, False)
                
                # 解析评估结果
                evaluation_result = self._parse_self_evaluation(evaluation_response)
                
                # 检查是否需要继续
                if not evaluation_result.get("should_continue", False):
                    self.logger.info(f"✅ 自主继续完成，任务已满足要求")
                    break
                
                # 构建继续提示
                continuation_prompt = self._build_continuation_prompt(evaluation_result)
                
                # 使用优化的LLM调用进行任务继续
                continuation_response = await self._call_llm_optimized(continuation_prompt, False)
                
                # 更新当前结果
                current_result = continuation_response
                
                self.logger.info(f"🔄 自主继续完成第 {self_iteration + 1} 轮")
                
            except Exception as e:
                self.logger.error(f"❌ 自主继续迭代失败: {str(e)}")
                break
        
        return current_result
    
    def get_llm_optimization_stats(self) -> Dict[str, Any]:
        """获取LLM优化统计信息"""
        if hasattr(self.llm_client, 'get_optimization_stats'):
            return self.llm_client.get_optimization_stats()
        return {"error": "LLM客户端不支持优化统计"}
    
    def clear_llm_context(self, conversation_id: str = None):
        """清除LLM对话上下文"""
        target_id = conversation_id or self.current_conversation_id
        if target_id and hasattr(self.llm_client, 'clear_conversation_context'):
            self.llm_client.clear_conversation_context(target_id)
            self.logger.info(f"🗑️ 清除LLM对话上下文: {target_id}")
    
    def clear_all_llm_contexts(self):
        """清除所有LLM对话上下文"""
        if hasattr(self.llm_client, 'clear_all_contexts'):
            self.llm_client.clear_all_contexts()
            self.logger.info("🗑️ 清除所有LLM对话上下文")
    
    async def _execute_single_task_cycle(self, conversation: List[Dict[str, str]], user_request: str, max_iterations: int) -> str:
        """执行单个任务周期（原有的Function Calling逻辑）"""
        
        for iteration in range(max_iterations):
            self.logger.info(f"🔄 Function Calling 迭代 {iteration + 1}/{max_iterations}")
            
            try:
                # 调用LLM
                llm_response = await self._call_llm_for_function_calling(conversation)
                
                # 解析工具调用
                tool_calls = self._parse_tool_calls_from_response(llm_response)
                
                if not tool_calls:
                    # 没有工具调用，返回最终结果
                    conversation.append({"role": "assistant", "content": llm_response})
                    # 🧠 更新并保存最终对话历史
                    self.conversation_history = conversation.copy()
                    self.logger.info(f"✅ 任务完成，无需调用工具。最终对话历史: {len(self.conversation_history)} 条消息")
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
                
                # 🧠 更新对话历史
                self.conversation_history = conversation.copy()
                self.logger.debug(f"💾 对话历史已更新: {len(self.conversation_history)} 条消息")
                
            except Exception as e:
                self.logger.error(f"❌ Function Calling迭代失败: {str(e)}")
                return f"处理请求时发生错误: {str(e)}"
        
        # 达到最大迭代次数，获取最终响应
        try:
            final_response = await self._call_llm_for_function_calling(conversation)
            # 🧠 保存最终对话状态
            conversation.append({"role": "assistant", "content": final_response})
            self.conversation_history = conversation.copy()
            self.logger.warning(f"⏰ 达到最大迭代次数。最终对话历史: {len(self.conversation_history)} 条消息")
            return final_response
        except Exception as e:
            error_msg = f"无法完成请求，已达到最大迭代次数: {str(e)}"
            # 🧠 记录错误状态
            conversation.append({"role": "assistant", "content": error_msg})
            self.conversation_history = conversation.copy()
            return error_msg
    
    async def _execute_self_continuation(self, conversation: List[Dict[str, str]], initial_result: str, 
                                       original_request: str, max_self_iterations: int, max_iterations: int) -> str:
        """执行自主任务继续逻辑"""
        self.logger.info(f"🧠 开始自主任务继续评估...")
        
        current_result = initial_result
        
        for self_iteration in range(max_self_iterations):
            self.logger.info(f"🔄 自主继续迭代 {self_iteration + 1}/{max_self_iterations}")
            
            # 🧠 构建自我评估prompt
            self_evaluation_prompt = self._build_self_evaluation_prompt(original_request, current_result)
            
            # 添加自我评估消息到对话
            conversation.append({"role": "user", "content": self_evaluation_prompt})
            
            try:
                # 获取LLM的自我评估和决策
                evaluation_response = await self._call_llm_for_function_calling(conversation)
                conversation.append({"role": "assistant", "content": evaluation_response})
                
                # 🧠 解析自我评估结果
                evaluation_result = self._parse_self_evaluation(evaluation_response)
                
                self.logger.info(f"📋 自我评估结果: {evaluation_result}")
                
                if evaluation_result["needs_continuation"]:
                    self.logger.info(f"🔄 决定继续执行任务: {evaluation_result['reason']}")
                    
                    # 构建继续任务的prompt
                    continuation_prompt = self._build_continuation_prompt(evaluation_result)
                    conversation.append({"role": "user", "content": continuation_prompt})
                    
                    # 执行继续任务
                    continuation_result = await self._execute_single_task_cycle(conversation, continuation_prompt, max_iterations)
                    current_result = continuation_result
                    
                    # 更新对话历史
                    self.conversation_history = conversation.copy()
                    
                else:
                    self.logger.info(f"✅ 任务评估完成，无需继续: {evaluation_result['reason']}")
                    # 更新对话历史并返回最终结果
                    self.conversation_history = conversation.copy()
                    return current_result
                    
            except Exception as e:
                self.logger.error(f"❌ 自主继续迭代失败: {str(e)}")
                return current_result
        
        self.logger.warning(f"⏰ 达到自主继续最大迭代次数")
        self.conversation_history = conversation.copy()
        return current_result
    
    def _build_self_evaluation_prompt(self, original_request: str, current_result: str) -> str:
        """构建自我评估prompt"""
        return f"""
## 🧠 任务完成度自我评估

**原始任务**: {original_request}

**当前完成情况**: 
{current_result}

请仔细分析当前的任务完成情况，并回答以下问题：

1. **任务完成度评估**: 原始任务是否已经完全完成？
2. **质量评估**: 当前的实现质量如何？是否存在可以改进的地方？
3. **遗漏分析**: 是否有遗漏的重要功能或步骤？
4. **继续决策**: 是否需要继续执行额外的任务来提高完成度或质量？

请用以下JSON格式回答：
```json
{{
    "completion_rate": 85,
    "quality_score": 80,
    "needs_continuation": true,
    "reason": "需要添加更详细的测试用例和错误处理",
    "suggested_next_actions": [
        "添加边界条件测试",
        "完善错误处理机制",
        "优化代码结构"
    ]
}}
```

如果任务已经完全完成且质量满意，请设置 `needs_continuation: false`。
"""
    
    def _parse_self_evaluation(self, response: str, tool_execution_summary: Dict[str, Any] = None) -> Dict[str, Any]:
        """解析自我评估结果"""
        try:
            # 🔧 修复：首先检查工具执行结果，如果有关键工具失败，强制继续
            has_critical_failures = False
            if tool_execution_summary and "failed_tools" in tool_execution_summary:
                critical_tools = ["generate_verilog_code", "write_file", "generate_testbench", "run_simulation"]
                failed_tools = tool_execution_summary["failed_tools"]
                has_critical_failures = any(tool in failed_tools for tool in critical_tools)
                
                if has_critical_failures:
                    self.logger.warning(f"⚠️ 检测到关键工具执行失败: {failed_tools}, 强制需要继续")
                    return {
                        "completion_rate": 30,
                        "quality_score": 50,
                        "needs_continuation": True,
                        "reason": f"关键工具执行失败: {', '.join(failed_tools)}，必须重新执行才能完成任务",
                        "suggested_actions": [f"修复并重新调用失败的工具: {tool}" for tool in failed_tools if tool in critical_tools]
                    }
            
            # 尝试解析JSON格式
            import json
            import re
            
            # 查找JSON代码块
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                evaluation_data = json.loads(matches[0])
                llm_evaluation = {
                    "completion_rate": evaluation_data.get("completion_rate", 100),
                    "quality_score": evaluation_data.get("quality_score", 100),
                    "needs_continuation": evaluation_data.get("needs_continuation", False),
                    "reason": evaluation_data.get("reason", "评估完成"),
                    "suggested_actions": evaluation_data.get("suggested_next_actions", [])
                }
                
                # 🔧 修复：如果有工具失败但LLM认为完成了，修正评估结果
                if has_critical_failures and not llm_evaluation["needs_continuation"]:
                    self.logger.warning(f"⚠️ LLM错误评估：工具失败但认为任务完成，修正评估结果")
                    llm_evaluation["needs_continuation"] = True
                    llm_evaluation["completion_rate"] = min(llm_evaluation["completion_rate"], 60)
                    llm_evaluation["reason"] = "工具执行失败，需要重新执行"
                
                return llm_evaluation
            
            # 如果没有找到JSON，尝试文本分析
            needs_continuation = any(phrase in response.lower() for phrase in [
                "需要继续", "未完成", "可以改进", "建议添加", "needs_continuation: true"
            ])
            
            # 工具失败时强制继续
            if has_critical_failures:
                needs_continuation = True
            
            return {
                "completion_rate": 60 if has_critical_failures else 90,
                "quality_score": 40 if has_critical_failures else 85,
                "needs_continuation": needs_continuation,
                "reason": "关键工具执行失败，需要重新执行" if has_critical_failures else "基于文本分析的评估结果",
                "suggested_actions": []
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ 自我评估解析失败: {str(e)}")
            # 默认不继续，返回保守的评估结果
            return {
                "completion_rate": 100,
                "quality_score": 90,
                "needs_continuation": False,
                "reason": "解析失败，采用保守策略",
                "suggested_actions": []
            }
    
    def _build_continuation_prompt(self, evaluation_result: Dict[str, Any]) -> str:
        """构建继续任务的prompt"""
        suggested_actions = evaluation_result.get("suggested_actions", [])
        reason = evaluation_result.get("reason", "继续改进任务")
        
        actions_text = "\n".join([f"- {action}" for action in suggested_actions]) if suggested_actions else "- 根据之前的分析继续改进"
        
        return f"""
## 🔄 继续任务执行

基于刚才的自我评估，我需要继续改进当前的工作。

**继续原因**: {reason}

**具体行动计划**:
{actions_text}

请继续执行这些改进任务，使用合适的工具来完成。
"""
    
    def _parse_tool_calls_from_response(self, response: str) -> List[ToolCall]:
        """解析LLM响应中的工具调用"""
        tool_calls = []
        
        self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 开始解析工具调用 - 响应长度: {len(response)}")
        self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 响应前500字: {response[:500]}...")
        
        # 基础检查
        has_tool_calls_key = "tool_calls" in response
        has_json_structure = response.strip().startswith('{') and response.strip().endswith('}')
        has_json_block = "```json" in response
        self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 初步检查 - tool_calls关键字: {has_tool_calls_key}, JSON结构: {has_json_structure}, JSON代码块: {has_json_block}")
        
        try:
            # 方法1: 直接解析JSON格式
            cleaned_response = response.strip()
            if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 方法1: 尝试直接解析JSON")
                try:
                    data = json.loads(cleaned_response)
                    self.logger.info(f"🔍 [TOOL_CALL_DEBUG] JSON解析成功 - 顶级键: {list(data.keys())}")
                    if 'tool_calls' in data and isinstance(data['tool_calls'], list):
                        self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 找到tool_calls数组 - 长度: {len(data['tool_calls'])}")
                        for i, tool_call_data in enumerate(data['tool_calls']):
                            if isinstance(tool_call_data, dict) and 'tool_name' in tool_call_data:
                                tool_call = ToolCall(
                                    tool_name=tool_call_data['tool_name'],
                                    parameters=tool_call_data.get('parameters', {}),
                                    call_id=tool_call_data.get('call_id', f"call_{len(tool_calls)}")
                                )
                                tool_calls.append(tool_call)
                                self.logger.info(f"🔧 [TOOL_CALL_DEBUG] 解析到工具调用 {i}: {tool_call.tool_name}")
                                self.logger.info(f"🔧 [TOOL_CALL_DEBUG] 参数: {list(tool_call.parameters.keys())}")
                            else:
                                self.logger.warning(f"⚠️ [TOOL_CALL_DEBUG] 工具调用 {i} 格式错误: {tool_call_data}")
                    else:
                        self.logger.warning(f"⚠️ [TOOL_CALL_DEBUG] 没有找到有效的tool_calls数组")
                except json.JSONDecodeError as e:
                    self.logger.warning(f"⚠️ [TOOL_CALL_DEBUG] JSON解析失败: {str(e)}")
            
            # 方法2: 查找JSON代码块
            if not tool_calls:
                self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 方法2: 查找JSON代码块")
                json_pattern = r'```json\s*(\{.*?\})\s*```'
                matches = re.findall(json_pattern, response, re.DOTALL)
                self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 找到 {len(matches)} 个JSON代码块")
                for i, match in enumerate(matches):
                    try:
                        data = json.loads(match)
                        if 'tool_calls' in data:
                            self.logger.info(f"🔍 [TOOL_CALL_DEBUG] JSON代码块 {i} 包含tool_calls")
                            for tool_call_data in data['tool_calls']:
                                tool_call = ToolCall(
                                    tool_name=tool_call_data['tool_name'],
                                    parameters=tool_call_data.get('parameters', {}),
                                    call_id=tool_call_data.get('call_id', f"call_{len(tool_calls)}")
                                )
                                tool_calls.append(tool_call)
                                self.logger.info(f"🔧 [TOOL_CALL_DEBUG] 从代码块解析到工具调用: {tool_call.tool_name}")
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"⚠️ [TOOL_CALL_DEBUG] JSON代码块 {i} 解析失败: {str(e)}")
                        continue
            
            # 方法3: 文本模式匹配备用方案
            if not tool_calls:
                self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 方法3: 文本模式匹配")
                tool_patterns = [
                    r'调用工具\s*[：:]\s*(\w+)',
                    r'使用工具\s*[：:]\s*(\w+)',
                    r'tool[：:]\s*(\w+)',
                    r'function[：:]\s*(\w+)'
                ]
                
                for pattern in tool_patterns:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    if matches:
                        self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 模式 '{pattern}' 匹配到 {len(matches)} 个工具")
                    for match in matches:
                        tool_call = ToolCall(
                            tool_name=match,
                            parameters={},
                            call_id=f"call_{len(tool_calls)}"
                        )
                        tool_calls.append(tool_call)
                        self.logger.info(f"🔧 [TOOL_CALL_DEBUG] 从文本中解析到工具调用: {tool_call.tool_name}")
            
            # 最终结果
            self.logger.info(f"✅ [TOOL_CALL_DEBUG] 解析完成 - 总计找到 {len(tool_calls)} 个工具调用")
            if not tool_calls:
                self.logger.warning(f"⚠️ [TOOL_CALL_DEBUG] 没有解析到任何工具调用！")
                # 提供调试信息
                if "write_file" in response.lower():
                    self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 响应中包含'write_file'但没有被解析为工具调用")
                if "generate_verilog" in response.lower():
                    self.logger.info(f"🔍 [TOOL_CALL_DEBUG] 响应中包含'generate_verilog'但没有被解析为工具调用")
            
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
            # 获取工具的实际函数签名
            if tool_name in self.function_calling_registry:
                tool_func = self.function_calling_registry[tool_name]
                import inspect
                
                # 获取函数签名
                sig = inspect.signature(tool_func)
                actual_params = list(sig.parameters.keys())
                
                self.logger.debug(f"🔍 工具 {tool_name} 实际参数: {actual_params}")
                self.logger.debug(f"🔍 传入参数: {list(parameters.keys())}")
                
                # 构建参数映射表
                param_mappings = self._build_parameter_mappings(tool_name, actual_params)
                
                # 应用映射
                normalized = parameters.copy()
                mapped_params = {}
                
                for input_param, value in normalized.items():
                    # 查找映射
                    mapped_param = param_mappings.get(input_param, input_param)
                    
                    if mapped_param != input_param:
                        self.logger.info(f"🔄 参数映射: {input_param} -> {mapped_param}")
                        mapped_params[mapped_param] = value
                    else:
                        mapped_params[input_param] = value
                
                # 验证映射后的参数是否在函数签名中
                invalid_params = []
                for param in mapped_params.keys():
                    if param not in actual_params and param != 'self':
                        invalid_params.append(param)
                
                if invalid_params:
                    self.logger.warning(f"⚠️ 工具 {tool_name} 存在无效参数: {invalid_params}")
                    # 移除无效参数
                    for invalid_param in invalid_params:
                        if invalid_param in mapped_params:
                            del mapped_params[invalid_param]
                            self.logger.info(f"🗑️ 移除无效参数: {invalid_param}")
                
                self.logger.debug(f"✅ 参数标准化完成: {list(mapped_params.keys())}")
                return mapped_params
                
            else:
                self.logger.warning(f"⚠️ 工具 {tool_name} 未找到，使用基本映射")
                return self._apply_basic_parameter_mapping(parameters)
                
        except Exception as e:
            self.logger.error(f"❌ 参数标准化失败: {str(e)}")
            return self._apply_basic_parameter_mapping(parameters)
    
    def _build_parameter_mappings(self, tool_name: str, actual_params: List[str]) -> Dict[str, str]:
        """构建参数映射表"""
        mappings = {}
        
        # 通用参数映射
        common_mappings = {
            # 代码相关参数
            "verilog_code": "module_code",
            "code": "module_code", 
            "design_code": "module_code",
            "rtl_code": "module_code",
            "source_code": "module_code",
            
            # 需求/描述相关参数 - 修复requirements参数映射
            "description": "requirements",
            "task_description": "requirements", 
            "design_requirements": "requirements",
            "specification": "requirements",
            "specs": "requirements",
            "behavior": "requirements",
            "functionality": "requirements",
            "design_spec": "requirements",
            
            # 模块名相关参数
            "name": "module_name",
            "module": "module_name",
            "target_module": "module_name",
            
            # 文件路径相关参数
            "file_path": "filename",
            "path": "filename",
            "filepath": "filename",
            
            # 测试相关参数
            "test_cases": "test_scenarios",
            "test_scenarios": "test_scenarios",  # 保持一致性
            "test_vectors": "test_scenarios",
            
            # 文件列表相关参数
            "files": "verilog_files",
            "design_files": "verilog_files",
            "source_files": "verilog_files",
            
            # 脚本相关参数
            "script": "script_name",
            "script_path": "script_name",
            
            # 覆盖率相关参数
            "coverage_file": "coverage_data_file",
            "coverage_data": "coverage_data_file",
        }
        
        # 工具特定的映射
        tool_specific_mappings = {
            "generate_testbench": {
                "verilog_code": "module_code",
                "code": "module_code",
                "design_code": "module_code",
                "test_cases": "test_scenarios",
                "test_vectors": "test_scenarios",
            },
            "run_simulation": {
                "module_file": "module_file",  # 保持原样
                "testbench_file": "testbench_file",  # 保持原样
                "module_code": "module_code",
                "testbench_code": "testbench_code",
            },
            "generate_build_script": {
                "verilog_files": "verilog_files",
                "design_files": "verilog_files",
                "source_files": "verilog_files",
                "testbench_files": "testbench_files",
            },
            "execute_build_script": {
                "script": "script_name",
                "script_path": "script_name",
            },
            "analyze_test_failures": {
                "design_code": "design_code",  # 保持原样
                "testbench_code": "testbench_code",  # 保持原样
            },
            "write_file": {
                "file_path": "filename",
                "path": "filename",
                "filepath": "filename",
            },
            "read_file": {
                "filepath": "filepath",  # 保持原样
                "path": "filepath",
                "file_path": "filepath",
            }
        }
        
        # 应用通用映射
        mappings.update(common_mappings)
        
        # 应用工具特定映射
        if tool_name in tool_specific_mappings:
            mappings.update(tool_specific_mappings[tool_name])
        
        # 验证映射的有效性
        valid_mappings = {}
        for input_param, mapped_param in mappings.items():
            if mapped_param in actual_params:
                valid_mappings[input_param] = mapped_param
            else:
                self.logger.debug(f"⚠️ 映射 {input_param} -> {mapped_param} 无效，目标参数不存在")
        
        return valid_mappings
    
    def _apply_basic_parameter_mapping(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """应用基本参数映射（备用方案）"""
        try:
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
            normalized = parameters.copy()
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
        
        # 🔧 TaskContext对话记录 - 工具调用开始
        if self.current_task_context and hasattr(self.current_task_context, 'add_conversation_message'):
            self.current_task_context.add_conversation_message(
                role="tool_call",
                content=f"开始调用工具: {tool_call.tool_name}",
                agent_id=self.agent_id,
                tool_info={
                    "tool_name": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "status": "started"
                }
            )
        
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
                
                # 🔧 TaskContext对话记录 - 工具调用成功
                if self.current_task_context and hasattr(self.current_task_context, 'add_conversation_message'):
                    self.current_task_context.add_conversation_message(
                        role="tool_result",
                        content=f"工具执行成功: {tool_call.tool_name}",
                        agent_id=self.agent_id,
                        tool_info={
                            "tool_name": tool_call.tool_name,
                            "parameters": tool_call.parameters,
                            "success": True,
                            "result": str(result)[:200] + ("..." if len(str(result)) > 200 else ""),  # 限制结果长度
                            "status": "completed"
                        }
                    )
                
                # 🆕 数据收集用于Gradio可视化
                if self.current_task_context:
                    import time
                    execution_timestamp = time.time()
                    
                    # 记录工具执行
                    self.current_task_context.tool_executions.append({
                        "timestamp": execution_timestamp,
                        "agent_id": self.agent_id,
                        "tool_name": tool_call.tool_name,
                        "parameters": tool_call.parameters,
                        "success": True,
                        "result_summary": str(result)[:100] + ("..." if len(str(result)) > 100 else ""),
                        "attempt": attempt + 1
                    })
                    
                    # 记录文件操作（如果是文件相关工具）
                    if tool_call.tool_name in ['write_file', 'read_file'] and isinstance(result, dict):
                        file_path = tool_call.parameters.get('file_path') or tool_call.parameters.get('filename')
                        if file_path:
                            self.current_task_context.file_operations.append({
                                "timestamp": execution_timestamp,
                                "agent_id": self.agent_id,
                                "operation": tool_call.tool_name,
                                "file_path": file_path,
                                "success": True,
                                "details": result.get('message', '')
                            })
                    
                    # 记录执行时间线
                    self.current_task_context.execution_timeline.append({
                        "timestamp": execution_timestamp,
                        "event_type": "tool_execution",
                        "agent_id": self.agent_id,
                        "description": f"{self.agent_id} 成功执行 {tool_call.tool_name}",
                        "details": {
                            "tool_name": tool_call.tool_name,
                            "success": True,
                            "attempt": attempt + 1
                        }
                    })
                
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
        
        # 所有重试都失败了，记录到TaskContext并返回增强的错误信息
        # 🔧 TaskContext对话记录 - 工具调用失败
        if self.current_task_context and hasattr(self.current_task_context, 'add_conversation_message'):
            self.current_task_context.add_conversation_message(
                role="tool_result",
                content=f"工具执行失败: {tool_call.tool_name}",
                agent_id=self.agent_id,
                tool_info={
                    "tool_name": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "success": False,
                    "error": last_error,
                    "retry_attempts": self.max_tool_retry_attempts,
                    "status": "failed"
                }
            )
            
        # 🆕 数据收集用于Gradio可视化 - 失败情况
        if self.current_task_context:
            import time
            failure_timestamp = time.time()
            
            # 记录工具执行失败
            self.current_task_context.tool_executions.append({
                "timestamp": failure_timestamp,
                "agent_id": self.agent_id,
                "tool_name": tool_call.tool_name,
                "parameters": tool_call.parameters,
                "success": False,
                "error": last_error,
                "retry_attempts": self.max_tool_retry_attempts
            })
            
            # 记录执行时间线 - 失败事件
            self.current_task_context.execution_timeline.append({
                "timestamp": failure_timestamp,
                "event_type": "tool_failure",
                "agent_id": self.agent_id,
                "description": f"{self.agent_id} 工具执行失败: {tool_call.tool_name}",
                "details": {
                    "tool_name": tool_call.tool_name,
                    "error": last_error,
                    "retry_attempts": self.max_tool_retry_attempts
                }
            })
        
        return ToolResult(
            call_id=tool_call.call_id or "unknown",
            success=False,
            result=None,
            error=f"工具执行失败 (已重试{self.max_tool_retry_attempts}次): {last_error}"
        )
    
    def _format_tool_results(self, tool_calls: List[ToolCall], tool_results: List[ToolResult]) -> str:
        """格式化工具执行结果 - 增强版，为LLM提供丰富的上下文信息"""
        result_message = "## 🔧 工具执行结果详细报告\n\n"
        
        # 统计信息
        total_calls = len(tool_calls)
        successful_calls = sum(1 for tr in tool_results if tr.success)
        failed_calls = total_calls - successful_calls
        
        result_message += f"📊 **当前轮次执行摘要**: {successful_calls}/{total_calls} 个工具成功执行"
        if failed_calls > 0:
            result_message += f" ({failed_calls} 个失败)"
        result_message += "\n\n"
        
        # 添加历史工具调用统计
        historical_summary = self._get_historical_tool_summary()
        if historical_summary:
            result_message += f"📈 **对话历史工具统计**: {historical_summary}\n\n"
        
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
                
                # 显示工具规范（如果可用）
                if hasattr(tool_result, 'tool_specification') and tool_result.tool_specification:
                    result_message += f"**工具规范**:\n```\n{tool_result.tool_specification}\n```\n"
                
                # 显示修复建议（如果可用）
                if hasattr(tool_result, 'suggested_fix') and tool_result.suggested_fix:
                    result_message += f"**修复建议**: {tool_result.suggested_fix}\n"
                
                # 如果有详细的错误上下文，显示它
                if hasattr(tool_result, 'context') and tool_result.context:
                    if isinstance(tool_result.context, dict) and 'detailed_error' in tool_result.context:
                        result_message += f"**详细分析**:\n```\n{tool_result.context['detailed_error']}\n```\n"
                
                result_message += f"**影响**: 此工具调用失败可能影响后续操作的执行\n"
                result_message += f"**建议**: 请根据工具规范和修复建议重新调用工具\n\n"
        
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
            result_message += "1. **查看工具规范**: 仔细阅读失败工具的工具规范，了解正确的参数格式\n"
            result_message += "2. **参考修复建议**: 根据提供的修复建议调整工具调用\n"
            result_message += "3. **重新调用工具**: 使用正确的参数格式重新调用失败的工具\n"
            result_message += "4. **检查工具可用性**: 确认工具名称是否正确，查看可用工具列表\n"
        
        result_message += "\n💭 **重要提示**: 请仔细分析上述结果，基于具体的成功/失败情况做出明智的下一步决策。"
        
        return result_message
    
    def _get_historical_tool_summary(self) -> str:
        """获取对话历史中的工具调用统计摘要"""
        if not self.conversation_history:
            return ""
        
        tool_calls_history = []
        tool_stats = {}
        
        # 遍历对话历史，提取工具调用信息
        for message in self.conversation_history:
            if message.get("role") == "user" and "工具执行结果详细报告" in message.get("content", ""):
                # 解析工具执行结果中的工具名称
                content = message.get("content", "")
                import re
                
                # 提取成功的工具调用
                success_pattern = r"### ✅ 工具 \d+: (\w+) - 执行成功"
                success_matches = re.findall(success_pattern, content)
                
                # 提取失败的工具调用
                failure_pattern = r"### ❌ 工具 \d+: (\w+) - 执行失败"
                failure_matches = re.findall(failure_pattern, content)
                
                for tool_name in success_matches:
                    if tool_name not in tool_stats:
                        tool_stats[tool_name] = {"success": 0, "failure": 0}
                    tool_stats[tool_name]["success"] += 1
                    
                for tool_name in failure_matches:
                    if tool_name not in tool_stats:
                        tool_stats[tool_name] = {"success": 0, "failure": 0}
                    tool_stats[tool_name]["failure"] += 1
        
        if not tool_stats:
            return ""
        
        # 格式化统计信息
        summary_parts = []
        total_success = sum(stats["success"] for stats in tool_stats.values())
        total_failure = sum(stats["failure"] for stats in tool_stats.values())
        total_calls = total_success + total_failure
        
        summary_parts.append(f"总计调用 {total_calls} 次工具 (成功: {total_success}, 失败: {total_failure})")
        
        # 按工具分类统计
        tool_summaries = []
        for tool_name, stats in sorted(tool_stats.items()):
            success_count = stats["success"]
            failure_count = stats["failure"]
            total_tool_calls = success_count + failure_count
            success_rate = (success_count / total_tool_calls * 100) if total_tool_calls > 0 else 0
            
            if failure_count > 0:
                tool_summaries.append(f"{tool_name}: {total_tool_calls}次 ({success_count}✅/{failure_count}❌, {success_rate:.0f}%成功率)")
            else:
                tool_summaries.append(f"{tool_name}: {total_tool_calls}次 (全部成功)")
        
        if tool_summaries:
            summary_parts.append(" | ".join(tool_summaries))
        
        return " - ".join(summary_parts)
    
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
                                file_type: str = "verilog") -> FileReference:
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
        
        # 对于Verilog文件，使用智能代码提取
        if file_type in ["verilog", "systemverilog"]:
            self.logger.info(f"🧹 使用智能代码提取处理Verilog文件")
            extracted_code = self.extract_verilog_code(cleaned_content)
            
            if extracted_code != cleaned_content:
                self.logger.info(f"🧹 Verilog代码提取成功：{len(cleaned_content)} -> {len(extracted_code)} 字符")
                cleaned_content = extracted_code
            else:
                self.logger.warning(f"⚠️ Verilog代码提取失败，使用传统清理方法")
                # 回退到传统清理方法
                cleaned_content = self._traditional_clean_content(cleaned_content)
        
        # 对于其他代码文件，使用传统清理方法
        elif file_type in ["python", "cpp", "c"]:
            cleaned_content = self._traditional_clean_content(cleaned_content)
        
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
    
    def _traditional_clean_content(self, content: str) -> str:
        """传统的文件内容清理方法"""
        cleaned_content = content.strip()
        lines = cleaned_content.split('\n')
        
        # 移除开头的```标记
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
            self.logger.debug(f"🧹 移除开头的markdown标记")
        
        # 移除结尾的```标记
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
            self.logger.debug(f"🧹 移除结尾的markdown标记")
        
        return '\n'.join(lines)
    def extract_verilog_code(self, content: str) -> str:
        """
        智能提取Verilog代码，从LLM响应中分离出纯代码部分
        
        Args:
            content: LLM的完整响应内容
            
        Returns:
            提取出的纯Verilog代码
        """
        self.logger.info(f"🔍 开始提取Verilog代码，原始内容长度: {len(content)}")
        
        # 方法1: 查找```verilog代码块
        verilog_blocks = []
        
        # 匹配```verilog或```v开头的代码块
        import re
        verilog_pattern = r'```(?:verilog|v)\s*\n(.*?)\n```'
        matches = re.findall(verilog_pattern, content, re.DOTALL)
        
        if matches:
            self.logger.info(f"✅ 找到 {len(matches)} 个Verilog代码块")
            for i, match in enumerate(matches):
                code = match.strip()
                if self._is_valid_verilog_code(code):
                    verilog_blocks.append(code)
                    self.logger.info(f"✅ 代码块 {i+1} 验证通过，长度: {len(code)}")
                else:
                    self.logger.warning(f"⚠️ 代码块 {i+1} 验证失败")
        
        # 方法2: 如果没有找到代码块，尝试提取module声明
        if not verilog_blocks:
            self.logger.info("🔍 未找到代码块，尝试提取module声明")
            module_pattern = r'module\s+\w+\s*\([^)]*\)[^;]*;.*?endmodule'
            module_matches = re.findall(module_pattern, content, re.DOTALL | re.IGNORECASE)
            
            if module_matches:
                self.logger.info(f"✅ 找到 {len(module_matches)} 个module声明")
                for i, match in enumerate(module_matches):
                    code = match.strip()
                    if self._is_valid_verilog_code(code):
                        verilog_blocks.append(code)
                        self.logger.info(f"✅ module {i+1} 验证通过，长度: {len(code)}")
                    else:
                        self.logger.warning(f"⚠️ module {i+1} 验证失败")
        
        # 方法3: 如果还是没有，尝试智能分割
        if not verilog_blocks:
            self.logger.info("🔍 尝试智能分割内容")
            lines = content.split('\n')
            code_lines = []
            in_code_section = False
            
            for line in lines:
                # 检测代码开始标记
                if any(marker in line.lower() for marker in ['module', '`timescale', '`include']):
                    in_code_section = True
                
                # 如果在代码段中，收集代码行
                if in_code_section:
                    # 跳过明显的非代码行
                    if not any(skip in line.lower() for skip in ['##', '---', '###', '**', '```']):
                        code_lines.append(line)
                
                # 检测代码结束标记
                if 'endmodule' in line.lower():
                    in_code_section = False
            
            if code_lines:
                code = '\n'.join(code_lines).strip()
                if self._is_valid_verilog_code(code):
                    verilog_blocks.append(code)
                    self.logger.info(f"✅ 智能分割成功，代码长度: {len(code)}")
        
        # 返回最长的有效代码块
        if verilog_blocks:
            best_code = max(verilog_blocks, key=len)
            self.logger.info(f"✅ 成功提取Verilog代码，长度: {len(best_code)}")
            return best_code
        else:
            self.logger.warning("⚠️ 未能提取到有效的Verilog代码")
            return content  # 返回原始内容作为后备
    
    def _is_valid_verilog_code(self, code: str) -> bool:
        """
        验证是否为有效的Verilog代码
        
        Args:
            code: 待验证的代码
            
        Returns:
            是否为有效代码
        """
        if not code or len(code.strip()) < 10:
            return False
        
        # 检查是否包含基本的Verilog语法元素
        verilog_keywords = [
            'module', 'endmodule', 'input', 'output', 'wire', 'reg',
            'assign', 'always', 'initial', 'begin', 'end', 'if', 'else',
            'case', 'default', 'parameter', 'localparam'
        ]
        
        code_lower = code.lower()
        keyword_count = sum(1 for keyword in verilog_keywords if keyword in code_lower)
        
        # 至少包含3个Verilog关键字
        if keyword_count < 3:
            return False
        
        # 检查是否包含module声明
        if 'module' not in code_lower:
            return False
        
        # 检查是否包含endmodule
        if 'endmodule' not in code_lower:
            return False
        
        # 检查是否包含过多的非代码内容
        non_code_indicators = ['##', '---', '###', '**', '```', '---', '===']
        non_code_count = sum(1 for indicator in non_code_indicators if indicator in code)
        
        if non_code_count > 5:  # 如果包含太多非代码标记，可能不是纯代码
            return False
        
        return True
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
    
    def clear_conversation_history(self):
        """清空对话历史 - 新增方法"""
        old_count = len(self.conversation_history)
        self.conversation_history.clear()
        self.current_conversation_id = None
        self.conversation_start_time = None
        self.logger.info(f"🧹 对话历史已清空: 删除了 {old_count} 条消息")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要 - 新增方法"""
        return {
            "conversation_id": self.current_conversation_id,
            "message_count": len(self.conversation_history),
            "conversation_duration": time.time() - (self.conversation_start_time or time.time()) if self.conversation_start_time else 0,
            "system_prompt_length": len(self.system_prompt),
            "last_message_time": self.conversation_start_time,
            "agent_id": self.agent_id,
            "role": self.role
        }
    
    # ==========================================================================
    # 🔧 基础Function Calling工具实现
    # ==========================================================================
    
    async def _tool_write_file(self, filename: str = None, content: str = None, directory: str = None, file_path: str = None, **kwargs) -> Dict[str, Any]:
        """基础工具：写入文件（增强版，支持中央文件管理）"""
        try:
            # 支持file_path参数作为filename的别名
            if file_path is not None and filename is None:
                filename = file_path
                self.logger.info(f"🔄 参数映射: file_path -> filename: {filename}")
            
            if filename is None:
                return {
                    "success": False,
                    "error": "缺少必需参数: filename 或 file_path"
                }
            
            if content is None:
                return {
                    "success": False,
                    "error": "缺少必需参数: content"
                }
            
            self.logger.info(f"📝 写入文件: {filename}")
            
            # 🆕 优先尝试使用当前任务上下文中的实验路径
            try:
                experiment_path = None
                
                # 1. 首先尝试从任务上下文获取实验路径
                if hasattr(self, 'current_task_context') and self.current_task_context:
                    task_context = self.current_task_context
                    if hasattr(task_context, 'experiment_path') and task_context.experiment_path:
                        experiment_path = Path(task_context.experiment_path)
                        self.logger.info(f"🧪 使用任务上下文实验路径: {experiment_path}")
                
                # 2. 如果任务上下文没有，尝试实验管理器
                if not experiment_path:
                    try:
                        from core.experiment_manager import get_experiment_manager
                        exp_manager = get_experiment_manager()
                        
                        self.logger.info(f"🔍 实验管理器检查:")
                        self.logger.info(f"   - 实验管理器存在: {exp_manager is not None}")
                        self.logger.info(f"   - 当前实验路径: {exp_manager.current_experiment_path if exp_manager else None}")
                        
                        if exp_manager and exp_manager.current_experiment_path:
                            experiment_path = Path(exp_manager.current_experiment_path)
                            self.logger.info(f"🧪 使用实验管理器路径: {experiment_path}")
                    except (ImportError, Exception) as e:
                        self.logger.debug(f"实验管理器不可用: {e}")
                
                # 3. 如果还是没有找到，尝试从活跃任务中查找
                if not experiment_path:
                    try:
                        # 尝试从协调智能体的活跃任务中获取实验路径
                        from core.llm_coordinator_agent import LLMCoordinatorAgent
                        if hasattr(self, 'coordinator') and isinstance(self.coordinator, LLMCoordinatorAgent):
                            for task in self.coordinator.active_tasks.values():
                                if hasattr(task, 'experiment_path') and task.experiment_path:
                                    experiment_path = Path(task.experiment_path)
                                    self.logger.info(f"🧪 从协调智能体活跃任务获取实验路径: {experiment_path}")
                                    break
                    except Exception as e:
                        self.logger.debug(f"从协调智能体获取实验路径失败: {e}")
                
                # 4. 如果有实验路径，直接保存到实验目录
                if experiment_path:
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
                    
                    # 创建目标目录并保存文件
                    exp_subdir_path = experiment_path / subdir
                    exp_subdir_path.mkdir(parents=True, exist_ok=True)
                    exp_file_path = exp_subdir_path / filename
                    
                    # 写入文件
                    with open(exp_file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    
                    # 尝试同时注册到中央文件管理器（可选）
                    try:
                        from core.file_manager import get_file_manager
                        file_manager = get_file_manager()
                        file_ref = file_manager.save_file(
                            content=cleaned_content,
                            filename=filename,
                            file_type=file_type,
                            created_by=self.agent_id,
                            description=f"由{self.agent_id}创建的{file_type}文件"
                        )
                        
                        self.logger.info(f"✅ 文件已保存到实验目录并注册到管理器: {exp_file_path}")
                        
                        return {
                            "success": True,
                            "message": f"文件 {filename} 已成功保存到实验目录",
                            "file_path": str(exp_file_path),
                            "file_id": file_ref.file_id,
                            "file_type": file_ref.file_type,
                            "filename": filename,
                            "content_length": len(cleaned_content),
                            "experiment_path": str(experiment_path),
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
                        # 即使中央管理器失败，文件已经保存到实验目录
                        return {
                            "success": True,
                            "message": f"文件 {filename} 已成功保存到实验目录",
                            "file_path": str(exp_file_path),
                            "file_id": None,
                            "file_type": file_type,
                            "filename": filename,
                            "content_length": len(cleaned_content),
                            "experiment_path": str(experiment_path),
                            "subdir": subdir
                        }
            except Exception as e:
                self.logger.warning(f"实验路径保存失败: {e}")
            
            # 回退到中央文件管理器
            try:
                from core.file_manager import get_file_manager
                file_manager = get_file_manager()
                self.logger.info(f"🔍 filename: {filename}")
                self.logger.info(f"🔍 file type: {self._detect_file_type(filename)}")
                
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
                
                self.logger.info(f"✅ 文件已通过中央管理器保存: {filename} (file path: {file_ref.file_path}) (ID: {file_ref.file_id})")
                
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

    def get_tool_specification(self, tool_name: str) -> str:
        """获取工具的完整规范"""
        specs = {
            "analyze_design_requirements": {
                "description": "分析Verilog设计需求，分解功能模块",
                "required_parameters": {
                    "requirements": "string - 设计需求描述",
                    "design_type": "string - 设计类型 (sequential/combinational)",
                    "complexity_level": "string - 复杂度级别 (low/medium/high)",
                    "module_name": "string - 模块名称"
                },
                "example": {
                    "requirements": "设计一个4位计数器",
                    "design_type": "sequential",
                    "complexity_level": "low",
                    "module_name": "counter"
                }
            },
            "generate_verilog_code": {
                "description": "生成Verilog模块代码",
                "required_parameters": {
                    "module_name": "string - 模块名称",
                    "behavior": "string - 模块行为描述"
                },
                "optional_parameters": {
                    "coding_style": "string - 编码风格 (synthesizable/non-blocking)",
                    "include_comments": "boolean - 是否包含注释"
                },
                "example": {
                    "module_name": "counter",
                    "behavior": "4位递增计数器，支持异步复位",
                    "coding_style": "synthesizable",
                    "include_comments": True
                }
            },
            "write_file": {
                "description": "保存内容到文件",
                "required_parameters": {
                    "file_path": "string - 文件路径",
                    "content": "string - 文件内容"
                },
                "optional_parameters": {
                    "file_type": "string - 文件类型 (verilog/testbench/report)"
                },
                "example": {
                    "file_path": "./designs/counter.v",
                    "content": "module counter(...); ... endmodule",
                    "file_type": "verilog"
                }
            },
            "read_file": {
                "description": "读取文件内容",
                "required_parameters": {
                    "file_path": "string - 文件路径"
                },
                "example": {
                    "file_path": "./designs/counter.v"
                }
            }
        }
        
        if tool_name in specs:
            spec = specs[tool_name]
            spec_text = f"工具名称: {tool_name}\n"
            spec_text += f"描述: {spec['description']}\n\n"
            
            spec_text += "必需参数:\n"
            for param, desc in spec['required_parameters'].items():
                spec_text += f"  - {param}: {desc}\n"
            
            if 'optional_parameters' in spec:
                spec_text += "\n可选参数:\n"
                for param, desc in spec['optional_parameters'].items():
                    spec_text += f"  - {param}: {desc}\n"
            
            spec_text += "\n使用示例:\n"
            spec_text += f"```json\n{json.dumps(spec['example'], indent=2, ensure_ascii=False)}\n```"
            
            return spec_text
        else:
            return f"工具 '{tool_name}' 的规范未找到。可用工具: {list(specs.keys())}"

    def get_suggested_fix(self, tool_name: str, error: str) -> str:
        """根据错误信息生成修复建议"""
        error_lower = error.lower()
        
        if "参数" in error or "parameter" in error_lower:
            return f"请检查 {tool_name} 的参数格式，参考工具规范重新调用。"
        elif "不存在" in error or "not found" in error_lower:
            return f"工具 {tool_name} 不存在，请使用正确的工具名称。"
        elif "文件" in error or "file" in error_lower:
            return f"文件路径错误，请检查路径是否正确。"
        else:
            return f"工具 {tool_name} 执行失败，请检查参数和调用方式。"

    async def _execute_tool_call_with_retry(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用，失败时返回给智能体处理"""
        try:
            self.logger.info(f"🔧 执行工具调用: {tool_call.tool_name}")
            
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
                tool_spec = self.get_tool_specification(tool_call.tool_name)
                suggested_fix = self.get_suggested_fix(tool_call.tool_name, f"工具 '{tool_call.tool_name}' 不存在")
                
                return ToolResult(
                    call_id=tool_call.call_id or "unknown",
                    success=False,
                    result=None,
                    error=f"工具 '{tool_call.tool_name}' 不存在。可用工具: {list(self.function_calling_registry.keys())}",
                    tool_specification=tool_spec,
                    suggested_fix=suggested_fix,
                    context={
                        "available_tools": list(self.function_calling_registry.keys()),
                        "called_tool": tool_call.tool_name
                    }
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
                
                # 如果工具内部报告失败，记录并抛出异常
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
            error_msg = str(e)
            self.logger.warning(f"⚠️ 工具执行失败 {tool_call.tool_name}: {error_msg}")
            
            # 记录详细的失败上下文
            failure_context = {
                "tool_name": tool_call.tool_name,
                "parameters": tool_call.parameters,
                "error": error_msg,
                "error_type": type(e).__name__,
                "timestamp": time.time(),
                "agent_id": self.agent_id,
                "role": self.role
            }
            
            # 增强错误信息格式
            detailed_error = await self._enhance_error_with_context(failure_context)
            failure_context["detailed_error"] = detailed_error
            
            self.tool_failure_contexts.append(failure_context)
            
            # 获取工具规范和修复建议
            tool_spec = self.get_tool_specification(tool_call.tool_name)
            suggested_fix = self.get_suggested_fix(tool_call.tool_name, error_msg)
            
            self.logger.error(f"❌ 工具调用失败 {tool_call.tool_name}: {error_msg}")
            self.logger.info(f"📋 返回工具规范给智能体处理")
            
            # 返回给智能体处理，不进行重试
            return ToolResult(
                call_id=tool_call.call_id or "unknown",
                success=False,
                result=None,
                error=error_msg,
                tool_specification=tool_spec,
                suggested_fix=suggested_fix,
                context=failure_context
            )

    async def handle_tool_failure(self, tool_result: ToolResult) -> str:
        """智能体处理工具失败，返回给LLM的提示信息"""
        if not tool_result.success:
            # 构建包含工具规范的提示
            retry_prompt = f"""
工具调用失败: {tool_result.error}

工具规范:
{tool_result.tool_specification or "工具规范未找到"}

修复建议:
{tool_result.suggested_fix or "无具体修复建议"}

请根据上述信息重新调用工具，确保：
1. 使用正确的工具名称
2. 按照工具规范提供正确的参数格式
3. 参考修复建议调整调用方式
"""
            return retry_prompt
        return "工具调用成功"