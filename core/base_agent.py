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
from config.config import FrameworkConfig

# 🔧 新增：导入已分解的组件
from .context.agent_context import AgentContext
from .conversation.manager import ConversationManager
from .function_calling.parser import ToolCallParser
from .function_calling.executor import ToolExecutionEngine, ExecutionContext
from .error_analysis.analyzer import ErrorAnalyzer
from .file_operations.manager import FileOperationManager, FileOperationConfig
from .types import FileReference, TaskMessage


class BaseAgent(ABC):
    """基础智能体类 - 支持Function Calling"""
    
    def __init__(self, agent_id: str, role: str = None, capabilities: Set[AgentCapability] = None):
        self.agent_id = agent_id
        self.role = role or "base_agent"
        self._capabilities = capabilities or set()
        self.status = AgentStatus.IDLE
        
        # 初始化配置
        self.config = FrameworkConfig.from_env()
        

        
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
        
        # 🔧 新增：初始化组件
        self.agent_context = AgentContext(
            agent_id=agent_id,
            role=role,
            capabilities=capabilities or set()
        )
        self.conversation_manager = ConversationManager(agent_id, self.logger)
        self.tool_call_parser = ToolCallParser(self.logger)
        
        # Function Calling配置
        self.max_tool_retry_attempts = 3
        self.tool_failure_contexts: List[Dict[str, Any]] = []
        
        # 🔧 任务上下文支持 - 用于协调器集成
        self.current_task_context: Optional[Any] = None  # TaskContext实例
        
        # 初始化新的组件
        execution_context = ExecutionContext(
            agent_id=agent_id,
            max_retry_attempts=self.max_tool_retry_attempts,
            task_context=self.current_task_context
        )
        self.tool_execution_engine = ToolExecutionEngine(execution_context, self.logger)
        self.error_analyzer = ErrorAnalyzer(self.logger)
        
        file_config = FileOperationConfig(
            default_artifacts_dir=str(self.default_artifacts_dir)
        )
        self.file_operation_manager = FileOperationManager(file_config, self.logger)
        
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
        
        # 注册Function Calling工具
        self._register_function_calling_tools()
        
        # 将工具注册到执行引擎
        self.tool_execution_engine.register_tools(self.function_calling_registry)
        
        # 生成system prompt (包含工具信息) - 延迟初始化
        self.system_prompt = None
        
        self.logger.debug(f"✅ {self.__class__.__name__} (Function Calling支持) 初始化完成")
    
    def _get_model_name(self) -> str:
        """从配置中获取模型名称"""
        return getattr(self.config.llm, 'model_name', 'claude-3.5-sonnet')
    
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
        # 为了向后兼容，同时存储两种格式
        # 1. 完整信息格式（用于ToolExecutionEngine）
        self.function_calling_registry[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {}
        }
        # 2. 直接函数格式（用于向后兼容）
        self._function_registry_backup = getattr(self, '_function_registry_backup', {})
        self._function_registry_backup[name] = func
        
        self.function_descriptions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters or {}
        }
        self.logger.debug(f"🔧 注册Function Calling工具: {name}")
    
    def set_task_context(self, task_context):
        """设置任务上下文，用于协调器集成
        
        Args:
            task_context: TaskContext实例，包含对话历史管理功能
        """
        self.current_task_context = task_context
        if task_context:
            self.logger.info(f"🔗 设置任务上下文: {task_context.task_id}")
            
            # 🔧 更新FileOperationManager的默认目录为实验路径
            if hasattr(task_context, 'experiment_path') and task_context.experiment_path:
                experiment_path = Path(task_context.experiment_path)
                # 创建实验目录结构
                designs_dir = experiment_path / "designs"
                testbenches_dir = experiment_path / "testbenches"
                designs_dir.mkdir(parents=True, exist_ok=True)
                testbenches_dir.mkdir(parents=True, exist_ok=True)
                
                # 更新FileOperationManager配置
                new_config = FileOperationConfig(
                    default_artifacts_dir=str(designs_dir)
                )
                self.file_operation_manager.config = new_config
                self.logger.info(f"📁 更新文件操作目录为实验路径: {designs_dir}")
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
        self.logger.debug(f"🛠️ 传统工具调用已启用: 权限={len(permissions)}")
    
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
                    {"role": "system", "content": self.system_prompt or ""},
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
                {"role": "system", "content": self.system_prompt or ""},
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
        llm_start_time = time.time()
        
        try:
            # 获取system prompt
            system_prompt = self.system_prompt
            
            # 🎯 使用统一日志系统记录LLM调用开始
            from core.unified_logging_system import get_global_logging_system
            logging_system = get_global_logging_system()
            
            # 调用优化的LLM客户端
            response = await self.llm_client.send_prompt_optimized(
                conversation_id=self.current_conversation_id,
                user_message=user_message,
                system_prompt=system_prompt if is_first_call else None,  # 只在第一次调用时传递system prompt
                temperature=0.3,
                max_tokens=4000,
                force_refresh_system=is_first_call
            )
            
            # 计算持续时间
            duration = time.time() - llm_start_time
            conversation_id = getattr(self, 'current_conversation_id', f"{self.agent_id}_{int(time.time())}")
            
            # 记录详细的LLM对话 - 使用新的增强方法
            try:
                from core.unified_logging_system import get_global_logging_system
                logging_system = get_global_logging_system()
                logging_system.log_detailed_llm_conversation(
                    agent_id=self.agent_id,
                    model_name=self._get_model_name(),
                    system_prompt=system_prompt or "",
                    user_message=user_message,
                    assistant_response=response,
                    conversation_id=conversation_id,
                    duration=duration,
                    temperature=0.3,
                    max_tokens=4000,
                    is_first_call=is_first_call,
                    success=True
                )
                
                # 保持向后兼容的日志记录
                safe_response = response or ""
                logging_system.log_llm_call(
                    agent_id=self.agent_id,
                    model_name=self._get_model_name(),
                    user_message=user_message,
                    response=safe_response,
                    prompt_length=len(user_message),
                    response_length=len(safe_response),
                    duration=duration,
                    success=True,
                    conversation_id=conversation_id
                )
            except Exception as log_error:
                self.logger.warning(f"⚠️ 详细对话记录失败: {log_error}")
            
            return response
        except Exception as e:
            # 记录LLM调用失败
            duration = time.time() - llm_start_time
            conversation_id = getattr(self, 'current_conversation_id', f"{self.agent_id}_{int(time.time())}")
            error_info = {"error": str(e), "error_type": type(e).__name__}
            
            # 记录详细的失败LLM对话
            try:
                from core.unified_logging_system import get_global_logging_system
                logging_system = get_global_logging_system()
                logging_system.log_detailed_llm_conversation(
                    agent_id=self.agent_id,
                    model_name=self._get_model_name(),
                    system_prompt=system_prompt or "",
                    user_message=user_message,
                    assistant_response="[调用失败]",
                    conversation_id=conversation_id,
                    duration=duration,
                    temperature=0.3,
                    max_tokens=4000,
                    is_first_call=is_first_call,
                    success=False,
                    error_info=error_info
                )
                
                # 保持向后兼容的日志记录
                logging_system.log_llm_call(
                    agent_id=self.agent_id,
                    model_name=self._get_model_name(),
                    user_message=user_message,
                    response="",
                    prompt_length=len(user_message),
                    duration=duration,
                    success=False,
                    error_info=error_info,
                    conversation_id=conversation_id
                )
            except Exception as log_error:
                self.logger.warning(f"⚠️ 失败对话记录失败: {log_error}")
            
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
    
    async def _generate_task_completion_summary(self, conversation: List[Dict[str, str]], original_response: str) -> str:
        """生成任务完成的详细总结"""
        try:
            # 分析对话历史中的工具调用情况
            tool_calls_made = []
            files_created = []
            
            for msg in conversation:
                if msg.get("role") == "user" and "工具执行结果" in msg.get("content", ""):
                    # 从工具结果消息中提取工具调用信息
                    content = msg.get("content", "")
                    if "write_file" in content:
                        # 提取写入的文件名
                        import re
                        file_match = re.search(r'写入文件:\s*([^\s,]+)', content)
                        if file_match:
                            files_created.append(file_match.group(1))
                    
                    # 提取其他工具调用
                    if "工具:" in content:
                        tool_match = re.search(r'工具:\s*([^\s,]+)', content)
                        if tool_match:
                            tool_calls_made.append(tool_match.group(1))
            
            # 构建总结提示
            summary_prompt = f"""
请基于以下对话历史为用户生成一个详细的任务完成总结。原始响应只有{len(original_response)}个字符可能过于简短。

对话过程中调用的工具: {', '.join(set(tool_calls_made)) if tool_calls_made else '无'}
创建的文件: {', '.join(files_created) if files_created else '无'}
原始简短响应: {original_response}

请生成一个详细的任务完成总结，包括：
1. 完成的主要工作概述
2. 具体执行的操作和生成的内容
3. 创建的文件和其内容说明
4. 任务的关键成果和特点

请用中文回复，格式要清晰专业。
"""
            
            # 创建临时对话用于生成总结
            summary_conversation = [
                {"role": "system", "content": "你是一个专业的任务总结助手，能够基于对话历史生成详细的工作总结。"},
                {"role": "user", "content": summary_prompt}
            ]
            
            # 调用LLM生成详细总结
            summary_response = await self._call_llm_for_function_calling(summary_conversation)
            
            if summary_response and len(summary_response.strip()) > 50:
                return summary_response.strip()
            else:
                return original_response
                
        except Exception as e:
            self.logger.warning(f"⚠️ 生成任务总结时出错: {e}")
            return original_response
    
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
                # 记录LLM调用前的状态
                llm_start_time = time.time()
                conversation_length = len(conversation)
                is_first_call = (iteration == 0)
                
                # 准备LLM调用的日志信息
                from core.unified_logging_system import get_global_logging_system
                logging_system = get_global_logging_system()
                
                # 构建用户消息和系统提示
                system_prompt = conversation[0]["content"] if conversation and conversation[0]["role"] == "system" else ""
                user_messages = [msg["content"] for msg in conversation if msg["role"] == "user"]
                current_user_message = user_messages[-1] if user_messages else ""
                
                # 记录准备LLM调用的日志信息 
                self.logger.info(f"🔄 [{self.role.upper()}] 准备LLM调用 - 对话历史长度: {conversation_length}, assistant消息数: {len([m for m in conversation if m.get('role') == 'assistant'])}, 是否首次调用: {is_first_call}")
                self.logger.info(f"🤖 [{self.role.upper()}] 发起LLM调用 - 对话ID: {getattr(self, 'current_conversation_id', 'unknown')}")
                
                # 调用LLM
                llm_response = await self._call_llm_for_function_calling(conversation)
                
                # 🔧 修复：检查LLM响应是否为None
                if llm_response is None:
                    self.logger.error(f"❌ LLM返回了None响应")
                    llm_response = "LLM调用失败，未返回有效响应"
                
                # 计算持续时间
                duration = time.time() - llm_start_time
                conversation_id = getattr(self, 'current_conversation_id', f"{self.agent_id}_{int(time.time())}")
                
                self.logger.info(f"🔍 [{self.role.upper()}] LLM响应长度: {len(llm_response)}")
                
                # 记录详细的LLM对话
                try:
                    from core.unified_logging_system import get_global_logging_system
                    logging_system = get_global_logging_system()
                    logging_system.log_detailed_llm_conversation(
                        agent_id=self.agent_id,
                        model_name=self._get_model_name(),
                        system_prompt=system_prompt,
                        user_message=current_user_message,
                        assistant_response=llm_response,
                        conversation_id=conversation_id,
                        duration=duration,
                        is_first_call=is_first_call,
                        success=True
                    )
                except Exception as log_error:
                    self.logger.warning(f"⚠️ 详细对话记录失败: {log_error}")
                
                # 🆕 记录到TaskContext（如果可用）
                if hasattr(self, 'current_task_context') and self.current_task_context and hasattr(self.current_task_context, 'add_llm_conversation'):
                    self.current_task_context.add_llm_conversation(
                        agent_id=self.agent_id,
                        conversation_id=conversation_id,
                        system_prompt=system_prompt,
                        user_message=current_user_message,
                        assistant_response=llm_response,
                        model_name=self._get_model_name(),
                        duration=duration,
                        success=True,
                        is_first_call=is_first_call
                    )
                
                # 解析工具调用
                tool_calls = self._parse_tool_calls_from_response(llm_response)
                
                if not tool_calls:
                    # 没有工具调用，检查是否需要生成详细总结
                    final_response = llm_response
                    
                    # 如果响应太短（可能只是确认消息），尝试生成更详细的总结
                    if llm_response and len(llm_response.strip()) < 100:
                        self.logger.info(f"🔍 检测到短响应({len(llm_response)}字符)，尝试生成详细总结...")
                        try:
                            # 生成任务完成总结
                            summary_response = await self._generate_task_completion_summary(conversation, llm_response)
                            if summary_response and len(summary_response) > len(llm_response):
                                final_response = summary_response
                                self.logger.info(f"✅ 生成了更详细的总结({len(summary_response)}字符)")
                            else:
                                self.logger.warning("⚠️ 无法生成更详细的总结，使用原始响应")
                        except Exception as e:
                            self.logger.warning(f"⚠️ 生成详细总结失败: {e}")
                    
                    conversation.append({"role": "assistant", "content": final_response})
                    # 🧠 更新并保存最终对话历史
                    self.conversation_history = conversation.copy()
                    self.logger.info(f"✅ 任务完成，无需调用工具。最终对话历史: {len(self.conversation_history)} 条消息")
                    return final_response
                
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
            # 记录最终LLM调用的详细信息
            llm_start_time = time.time()
            conversation_id = getattr(self, 'current_conversation_id', f"{self.agent_id}_{int(time.time())}")
            
            final_response = await self._call_llm_for_function_calling(conversation)
            
            # 记录最终调用的详细日志
            duration = time.time() - llm_start_time
            
            try:
                from core.unified_logging_system import get_global_logging_system
                logging_system = get_global_logging_system()
                
                system_prompt = conversation[0]["content"] if conversation and conversation[0]["role"] == "system" else ""
                user_messages = [msg["content"] for msg in conversation if msg["role"] == "user"]
                current_user_message = user_messages[-1] if user_messages else ""
                
                logging_system.log_detailed_llm_conversation(
                    agent_id=self.agent_id,
                    model_name=self._get_model_name(),
                    system_prompt=system_prompt,
                    user_message=current_user_message,
                    assistant_response=final_response,
                    conversation_id=conversation_id,
                    duration=duration,
                    is_first_call=False,
                    success=True
                )
            except Exception as log_error:
                self.logger.warning(f"⚠️ 最终对话详细记录失败: {log_error}")
            
            # 🆕 记录到TaskContext（如果可用）
            if hasattr(self, 'current_task_context') and self.current_task_context and hasattr(self.current_task_context, 'add_llm_conversation'):
                self.current_task_context.add_llm_conversation(
                    agent_id=self.agent_id,
                    conversation_id=conversation_id,
                    system_prompt=system_prompt,
                    user_message=current_user_message,
                    assistant_response=final_response,
                    model_name=self._get_model_name(),
                    duration=duration,
                    success=True,
                    is_first_call=False
                )
            
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
        """解析自我评估结果 - 增强版，支持工具调用验证"""
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
            
            # 🆕 新增：工具调用验证机制
            tool_validation_result = self._validate_required_tool_calls()
            if tool_validation_result["needs_continuation"]:
                self.logger.warning(f"⚠️ 工具调用验证失败: {tool_validation_result['reason']}")
                return tool_validation_result
            
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
    
    def _validate_required_tool_calls(self) -> Dict[str, Any]:
        """验证必需的工具调用 - 增强版，支持循环检测"""
        try:
            # 获取工具调用历史
            tool_calls = self._extract_tool_calls_from_history()
            
            # 🆕 新增：循环检测
            loop_detection = self._detect_tool_call_loops(tool_calls)
            if loop_detection["is_loop"]:
                self.logger.warning(f"🔄 检测到工具调用循环: {loop_detection['pattern']}")
                return {
                    "needs_continuation": False,
                    "reason": f"检测到工具调用循环，强制停止: {loop_detection['pattern']}",
                    "suggested_actions": ["停止循环执行"]
                }
            
            # 🆕 新增：重复操作检测
            repetition_detection = self._detect_repetitive_operations(tool_calls)
            if repetition_detection["is_repetitive"]:
                self.logger.warning(f"🔄 检测到重复操作: {repetition_detection['pattern']}")
                return {
                    "needs_continuation": False,
                    "reason": f"检测到重复操作，强制停止: {repetition_detection['pattern']}",
                    "suggested_actions": ["停止重复执行"]
                }
            
            # 原有的工具调用验证逻辑
            agent_type = self.role.lower()
            agent_id = getattr(self, 'agent_id', '').lower()
            required_tools = self._get_required_tools_for_agent(agent_type)
            
            if not required_tools:
                return {"needs_continuation": False, "reason": "无需验证工具调用"}
            
            # 检查必需工具是否都被调用
            called_tools = [call["tool_name"] for call in tool_calls]
            missing_tools = [tool for tool in required_tools if tool not in called_tools]
            
            # 🔧 修复：针对协调智能体的特殊验证逻辑
            if "coordinator" in agent_type or "llm_coordinator" in agent_type or "llm_coordinator" in agent_id:
                # 检查是否调用了recommend_agent但没有调用assign_task_to_agent
                if "recommend_agent" in called_tools and "assign_task_to_agent" not in called_tools:
                    self.logger.warning(f"⚠️ 协调智能体调用了recommend_agent但未调用assign_task_to_agent")
                    return {
                        "needs_continuation": True,
                        "reason": "已推荐智能体但未分配任务，必须调用assign_task_to_agent工具",
                        "suggested_actions": ["调用assign_task_to_agent工具分配任务给推荐的智能体"]
                    }
                
                # 检查是否调用了identify_task_type但没有调用recommend_agent
                if "identify_task_type" in called_tools and "recommend_agent" not in called_tools:
                    self.logger.warning(f"⚠️ 协调智能体调用了identify_task_type但未调用recommend_agent")
                    return {
                        "needs_continuation": True,
                        "reason": "已识别任务类型但未推荐智能体，必须调用recommend_agent工具",
                        "suggested_actions": ["调用recommend_agent工具推荐合适的智能体"]
                    }
                
                # 检查是否调用了identify_task_type和recommend_agent，但缺少assign_task_to_agent
                if "identify_task_type" in called_tools and "recommend_agent" in called_tools and "assign_task_to_agent" not in called_tools:
                    self.logger.warning(f"⚠️ 协调智能体完成了前两步但未调用assign_task_to_agent")
                    return {
                        "needs_continuation": True,
                        "reason": "已完成任务识别和智能体推荐，但未分配任务，必须调用assign_task_to_agent工具",
                        "suggested_actions": ["调用assign_task_to_agent工具分配任务给推荐的智能体"]
                    }
            
            if missing_tools:
                self.logger.warning(f"⚠️ 缺少必需的工具调用: {missing_tools}")
                return {
                    "needs_continuation": True,
                    "reason": f"缺少必需的工具调用: {', '.join(missing_tools)}",
                    "suggested_actions": [f"调用必需工具: {tool}" for tool in missing_tools]
                }
            
            # 验证工具调用顺序
            order_validation = self._validate_tool_call_order(tool_calls, required_tools)
            if not order_validation["valid"]:
                return {
                    "needs_continuation": True,
                    "reason": f"工具调用顺序错误: {order_validation['reason']}",
                    "suggested_actions": ["按照正确顺序调用工具"]
                }
            
            return {"needs_continuation": False, "reason": "所有必需工具调用完成"}
            
        except Exception as e:
            self.logger.error(f"❌ 工具调用验证失败: {e}")
            return {"needs_continuation": False, "reason": f"验证过程出错: {e}"}
    
    def _detect_tool_call_loops(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检测工具调用循环模式"""
        if len(tool_calls) < 6:  # 至少需要6次调用才能形成循环
            return {"is_loop": False, "pattern": ""}
        
        # 分析最近的工具调用序列
        recent_calls = tool_calls[-6:]  # 分析最近6次调用
        call_sequence = [call["tool_name"] for call in recent_calls]
        
        # 检测重复模式
        patterns = [
            ["write_file", "analyze_code_quality", "write_file", "analyze_code_quality"],
            ["generate_verilog_code", "write_file", "analyze_code_quality"],
            ["write_file", "write_file", "analyze_code_quality"],
        ]
        
        for pattern in patterns:
            if self._sequence_contains_pattern(call_sequence, pattern):
                return {"is_loop": True, "pattern": " -> ".join(pattern)}
        
        return {"is_loop": False, "pattern": ""}
    
    def _detect_repetitive_operations(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检测重复操作"""
        if len(tool_calls) < 4:
            return {"is_repetitive": False, "pattern": ""}
        
        # 分析最近的工具调用
        recent_calls = tool_calls[-4:]
        call_names = [call["tool_name"] for call in recent_calls]
        
        # 检测连续重复
        if len(set(call_names)) == 1:  # 所有调用都是同一个工具
            return {"is_repetitive": True, "pattern": f"连续重复调用 {call_names[0]}"}
        
        # 检测交替重复
        if len(call_names) >= 4:
            if call_names[-4:] == call_names[-2:] * 2:  # 模式重复
                return {"is_repetitive": True, "pattern": f"交替重复: {' -> '.join(call_names[-2:])}"}
        
        return {"is_repetitive": False, "pattern": ""}
    
    def _sequence_contains_pattern(self, sequence: List[str], pattern: List[str]) -> bool:
        """检查序列是否包含指定模式"""
        if len(sequence) < len(pattern):
            return False
        
        # 检查序列末尾是否匹配模式
        return sequence[-len(pattern):] == pattern
    
    def _extract_tool_calls_from_history(self) -> List[Dict[str, Any]]:
        """从对话历史中提取工具调用记录 - 返回列表格式"""
        tool_calls = []
        
        if not self.conversation_history:
            return tool_calls
        
        for message in self.conversation_history:
            content = message.get("content", "")
            import re
            
            # 🔧 修复：从多种格式中提取工具调用
            # 1. 从工具执行结果详细报告中提取
            if "工具执行结果详细报告" in content:
                # 提取成功的工具调用
                success_pattern = r"### ✅ 工具 \d+: (\w+) - 执行成功"
                success_matches = re.findall(success_pattern, content)
                
                # 提取失败的工具调用
                failure_pattern = r"### ❌ 工具 \d+: (\w+) - 执行失败"
                failure_matches = re.findall(failure_pattern, content)
                
                # 记录成功的工具调用
                for tool_name in success_matches:
                    tool_calls.append({
                        "tool_name": tool_name,
                        "success": True,
                        "timestamp": message.get("timestamp", time.time())
                    })
                
                # 记录失败的工具调用
                for tool_name in failure_matches:
                    tool_calls.append({
                        "tool_name": tool_name,
                        "success": False,
                        "timestamp": message.get("timestamp", time.time())
                    })
            
            # 2. 从LLM响应中的工具调用JSON中提取
            if message.get("role") == "assistant":
                # 查找工具调用JSON
                tool_call_pattern = r'"tool_name":\s*"([^"]+)"'
                tool_matches = re.findall(tool_call_pattern, content)
                
                for tool_name in tool_matches:
                    # 检查是否已经记录过这个工具调用（基于工具名称去重，忽略时间戳）
                    existing_tool = next((call for call in tool_calls if call["tool_name"] == tool_name), None)
                    if not existing_tool:
                        tool_calls.append({
                            "tool_name": tool_name,
                            "success": True,  # 假设LLM响应中的工具调用是成功的
                            "timestamp": message.get("timestamp", time.time())
                        })
            
            # 3. 从工具执行日志中提取
            if "工具执行" in content or "Tool execution" in content:
                # 提取工具名称
                tool_pattern = r"工具\s*(\w+)\s*执行"  # 中文格式
                tool_matches = re.findall(tool_pattern, content)
                
                for tool_name in tool_matches:
                    if not any(call["tool_name"] == tool_name for call in tool_calls):
                        tool_calls.append({
                            "tool_name": tool_name,
                            "success": True,
                            "timestamp": message.get("timestamp", time.time())
                        })
        
        return tool_calls
    
    def _get_required_tools_for_agent(self, agent_type: str) -> List[str]:
        """根据智能体类型获取必需的工具调用列表"""
        # 定义各智能体类型的必需工具
        required_tools_config = {
            "verilog_designer": ["generate_verilog_code", "write_file", "analyze_code_quality"],
            "code_reviewer": ["generate_testbench", "run_simulation", "write_file"],
            "llm_coordinator": ["identify_task_type", "recommend_agent", "assign_task_to_agent"],
            "coordinator": ["identify_task_type", "recommend_agent", "assign_task_to_agent"]
        }
        
        return required_tools_config.get(agent_type, [])
    
    def _validate_tool_call_order(self, tool_calls: List[Dict[str, Any]], required_tools: List[str]) -> Dict[str, Any]:
        """验证工具调用顺序"""
        if not tool_calls or not required_tools:
            return {"valid": True, "reason": "无需验证顺序"}
        
        # 简化的顺序验证：检查关键工具是否按预期顺序调用
        called_tools = [call["tool_name"] for call in tool_calls]
        
        # 对于Verilog设计智能体，确保generate_verilog_code在write_file之前
        if "verilog_designer" in self.role.lower():
            if "write_file" in called_tools and "generate_verilog_code" in called_tools:
                write_index = called_tools.index("write_file")
                generate_index = called_tools.index("generate_verilog_code")
                if write_index < generate_index:
                    return {
                        "valid": False,
                        "reason": "write_file在generate_verilog_code之前调用"
                    }
        
        # 对于代码审查智能体，确保generate_testbench在run_simulation之前
        if "code_reviewer" in self.role.lower():
            if "run_simulation" in called_tools and "generate_testbench" in called_tools:
                sim_index = called_tools.index("run_simulation")
                testbench_index = called_tools.index("generate_testbench")
                if sim_index < testbench_index:
                    return {
                        "valid": False,
                        "reason": "run_simulation在generate_testbench之前调用"
                    }
        
        return {"valid": True, "reason": "工具调用顺序正确"}
    
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
        """解析LLM响应中的工具调用 - 使用ToolCallParser组件"""
        return self.tool_call_parser.parse_tool_calls_from_response(response)
    
    def _normalize_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """标准化工具参数 - 使用ToolCallParser组件"""
        return self.tool_call_parser.normalize_tool_parameters(tool_name, parameters)
    
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
        """执行工具调用 - 向后兼容版本"""
        import asyncio
        import time
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.max_tool_retry_attempts):
            try:
                self.logger.info(f"🔧 执行工具调用: {tool_call.tool_name} (尝试 {attempt + 1}/{self.max_tool_retry_attempts})")
                
                # 标准化参数
                normalized_parameters = self._normalize_tool_parameters(tool_call.tool_name, tool_call.parameters)
                if normalized_parameters != tool_call.parameters:
                    self.logger.info(f"🎯 {tool_call.tool_name} 参数已标准化")
                    tool_call = ToolCall(
                        tool_name=tool_call.tool_name,
                        parameters=normalized_parameters,
                        call_id=tool_call.call_id
                    )
                
                # 检查工具是否存在
                if tool_call.tool_name not in self._function_registry_backup:
                    return ToolResult(
                        call_id=tool_call.call_id or "unknown",
                        success=False,
                        result=None,
                        error=f"工具 '{tool_call.tool_name}' 不存在。可用工具: {list(self._function_registry_backup.keys())}"
                    )
                
                # 获取并执行工具函数
                tool_func = self._function_registry_backup[tool_call.tool_name]
                
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
                    
                    # 🚨 修复：检查是否为增强错误处理结果
                    if not tool_success and result.get('enhanced_error_info'):
                        # 这是增强错误处理的结果，不应该抛出异常
                        self.logger.info(f"🔍 检测到增强错误处理结果: {tool_call.tool_name}")
                        # 直接返回结果，不抛出异常
                    elif not tool_success:
                        # 这是普通的工具失败，抛出异常以触发重试
                        error_msg = tool_error or "工具内部执行失败"
                        self.logger.warning(f"⚠️ 工具内部报告失败 {tool_call.tool_name}: {error_msg}")
                        raise Exception(error_msg)
                
                # 记录成功的工具执行结果
                duration = time.time() - start_time
                try:
                    from core.unified_logging_system import get_global_logging_system
                    logging_system = get_global_logging_system()
                    logging_system.log_tool_result(
                        agent_id=self.agent_id,
                        tool_name=tool_call.tool_name,
                        success=True,
                        result=result,
                        duration=duration
                    )
                except Exception as log_error:
                    self.logger.warning(f"⚠️ 工具成功日志记录失败: {log_error}")
                
                return ToolResult(
                    call_id=tool_call.call_id or "unknown",
                    success=True,
                    result=result,
                    error=None
                )
                
            except Exception as e:
                last_error = str(e)
                duration = time.time() - start_time
                self.logger.warning(f"⚠️ 工具执行失败 {tool_call.tool_name} (尝试 {attempt + 1}): {str(e)}")
                
                # 记录详细的工具执行失败日志
                try:
                    from core.unified_logging_system import get_global_logging_system
                    logging_system = get_global_logging_system()
                    logging_system.log_tool_result(
                        agent_id=self.agent_id,
                        tool_name=tool_call.tool_name,
                        success=False,
                        error=str(e),
                        duration=duration
                    )
                except Exception as log_error:
                    self.logger.warning(f"⚠️ 工具失败日志记录失败: {log_error}")
                
                # 记录详细的失败上下文
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
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_tool_retry_attempts - 1:
                    self.logger.info(f"⏳ 等待 1 秒后重试...")
                    await asyncio.sleep(1)
                else:
                    self.logger.error(f"❌ 工具执行最终失败: {tool_call.tool_name}")
        
        # 所有重试都失败了
        return ToolResult(
            call_id=tool_call.call_id or "unknown",
            success=False,
            result=None,
            error=last_error or "工具执行失败"
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
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取智能体能力 - 使用AgentContext组件"""
        return self.agent_context.get_capabilities()
    
    def get_specialty_description(self) -> str:
        """获取专业描述 - 使用AgentContext组件"""
        return self.agent_context.get_specialty_description()
    
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
        """自主读取文件内容 - 使用FileOperationManager组件"""
        return await self.file_operation_manager.read_file(file_ref.file_path)
    
    async def save_result_to_file(self, content: str, file_path: str, 
                                file_type: str = "verilog") -> FileReference:
        """保存结果到文件 - 使用FileOperationManager组件"""
        file_ref = await self.file_operation_manager.write_file(
            content=content,
            file_path=file_path,
            file_type=file_type
        )
        if file_ref:
            # 更新元数据
            file_ref.metadata.update({
                "created_by": self.agent_id
            })
        return file_ref
    
    def _clean_file_content(self, content: str, file_type: str) -> str:
        """清理文件内容，移除不必要的格式标记"""
        cleaned_content = content.strip()
        
        # 对于Verilog文件，使用智能代码提取
        if file_type in ["verilog", "systemverilog"]:
            self.logger.info(f"🧹 使用智能代码提取处理Verilog文件")
            extracted_code = self.extract_verilog_code(cleaned_content)
            
            # 🎯 修复：检查提取的代码是否有效，而不是比较长度
            if extracted_code and len(extracted_code.strip()) > 0:
                # 检查是否包含Verilog关键字，确认是有效代码
                verilog_keywords = ['module', 'endmodule', 'input', 'output', 'wire', 'reg', 'always', 'assign']
                if any(keyword in extracted_code.lower() for keyword in verilog_keywords):
                    self.logger.info(f"🧹 Verilog代码提取成功：长度 {len(extracted_code)} 字符")
                    cleaned_content = extracted_code
                else:
                    self.logger.warning(f"⚠️ 提取的内容不包含Verilog关键字，使用传统清理方法")
                    cleaned_content = self._traditional_clean_content(cleaned_content)
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
            # 🎯 优化：检查原始内容是否已经是有效的Verilog代码
            if self._is_valid_verilog_code(content):
                self.logger.info(f"✅ 原始内容已经是有效的Verilog代码，长度: {len(content)}")
                return content
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
        """获取智能体状态 - 使用AgentContext组件"""
        # 获取组件状态
        context_status = self.agent_context.to_dict()
        
        # 合并原有状态
        status = {
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self._capabilities],
            "task_count": len(self.task_history),
            "cache_size": len(self.file_cache)
        }
        
        # 合并组件状态
        status.update(context_status)
        return status
    
    def clear_cache(self):
        """清空缓存"""
        self.file_cache.clear()
        self.file_metadata_cache.clear()
        self.logger.info("🧹 缓存已清空")
    
    def clear_conversation_history(self):
        """清空对话历史 - 使用ConversationManager组件"""
        old_count = len(self.conversation_history)
        self.conversation_manager.clear_all_conversations()
        self.conversation_history.clear()
        self.current_conversation_id = None
        self.conversation_start_time = None
        self.logger.info(f"🧹 对话历史已清空: 删除了 {old_count} 条消息")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要 - 使用ConversationManager组件"""
        # 获取组件管理的对话摘要
        component_summary = self.conversation_manager.get_all_conversations_summary()
        
        # 合并原有的摘要信息
        summary = {
            "conversation_id": self.current_conversation_id,
            "message_count": len(self.conversation_history),
            "conversation_duration": time.time() - (self.conversation_start_time or time.time()) if self.conversation_start_time else 0,
            "system_prompt_length": len(self.system_prompt),
            "last_message_time": self.conversation_start_time,
            "agent_id": self.agent_id,
            "role": self.role
        }
        
        # 合并组件摘要
        summary.update(component_summary)
        return summary
    
    # ==========================================================================
    # 🔧 基础Function Calling工具实现
    # ==========================================================================
    
    async def _tool_write_file(self, filename: str = None, content: str = None, directory: str = None, file_path: str = None, **kwargs) -> Dict[str, Any]:
        """基础工具：写入文件 - 使用FileOperationManager组件"""
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
        
        # 使用FileOperationManager组件
        file_ref = await self.file_operation_manager.write_file(
            filename=filename,
            content=content,
            directory=directory
        )
        
        if file_ref is not None:
            return {
                "success": True,
                "file_path": file_ref.file_path,
                "file_type": file_ref.file_type,
                "description": file_ref.description,
                "metadata": file_ref.metadata
            }
        else:
            return {
                "success": False,
                "error": f"写入文件失败: {filename}",
                "filename": filename
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
        """基础工具：读取文件 - 使用FileOperationManager组件"""
        self.logger.info(f"📖 读取文件: {filepath}")
        
        # 使用FileOperationManager组件
        content = await self.file_operation_manager.read_file(
            file_path=filepath
        )
        
        if content is not None:
            return {
                "success": True,
                "content": content,
                "file_path": filepath,
                "content_length": len(content)
            }
        else:
            return {
                "success": False,
                "error": f"无法读取文件: {filepath}",
                "file_path": filepath
            }
    
    # ==========================================================================
    # 🚨 错误处理增强方法 - 修复缺失的关键功能
    # ==========================================================================
    
    async def _enhance_error_with_context(self, failure_context: Dict[str, Any]) -> str:
        """增强错误信息，基于上下文生成详细分析 - 使用ErrorAnalyzer组件"""
        return await self.error_analyzer.enhance_error_with_context(
            failure_context, 
            max_retry_attempts=self.max_tool_retry_attempts
        )
    
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