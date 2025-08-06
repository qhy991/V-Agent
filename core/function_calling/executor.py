#!/usr/bin/env python3
"""
Tool Execution Engine - 工具执行引擎
====================================

从BaseAgent中提取的工具执行功能，负责执行工具调用、重试机制和错误处理。
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .parser import ToolCall, ToolResult


@dataclass
class ExecutionContext:
    """执行上下文"""
    agent_id: str
    max_retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_logging: bool = True
    task_context: Optional[Any] = None


class ToolExecutionEngine:
    """工具执行引擎"""
    
    def __init__(self, context: ExecutionContext, logger: Optional[logging.Logger] = None):
        self.context = context
        self.logger = logger or logging.getLogger(__name__)
        
        # 工具注册表
        self.tool_registry: Dict[str, Any] = {}
        
        # 执行统计
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_retries': 0,
            'average_execution_time': 0.0
        }
    
    def register_tool(self, name: str, func: Any, description: str = "", parameters: Dict[str, Any] = None):
        """注册工具"""
        self.tool_registry[name] = {
            'func': func,
            'description': description,
            'parameters': parameters or {}
        }
        self.logger.debug(f"🔧 注册工具: {name}")
    
    def register_tools(self, tools: Dict[str, Dict[str, Any]]):
        """批量注册工具"""
        for name, tool_info in tools.items():
            self.register_tool(
                name=name,
                func=tool_info.get('func'),
                description=tool_info.get('description', ''),
                parameters=tool_info.get('parameters', {})
            )
    
    async def execute_tool_call(self, tool_call: ToolCall, parameter_normalizer=None) -> ToolResult:
        """执行工具调用（带重试机制）"""
        start_time = time.time()
        last_error = None
        
        # 记录执行开始
        self._log_execution_start(tool_call)
        
        for attempt in range(self.context.max_retry_attempts):
            try:
                self.logger.info(f"🔧 执行工具调用: {tool_call.tool_name} (尝试 {attempt + 1}/{self.context.max_retry_attempts})")
                
                # 标准化参数
                if parameter_normalizer:
                    normalized_parameters = parameter_normalizer(tool_call.tool_name, tool_call.parameters)
                    if normalized_parameters != tool_call.parameters:
                        self.logger.info(f"🎯 {tool_call.tool_name} 参数已标准化")
                        tool_call = ToolCall(
                            tool_name=tool_call.tool_name,
                            parameters=normalized_parameters,
                            call_id=tool_call.call_id
                        )
                
                # 检查工具是否存在
                if tool_call.tool_name not in self.tool_registry:
                    return ToolResult(
                        call_id=tool_call.call_id or "unknown",
                        success=False,
                        result=None,
                        error=f"工具 '{tool_call.tool_name}' 不存在。可用工具: {list(self.tool_registry.keys())}"
                    )
                
                # 获取并执行工具函数
                tool_func = self.tool_registry[tool_call.tool_name]['func']
                
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
                
                # 记录执行成功
                execution_time = time.time() - start_time
                self._log_execution_success(tool_call, result, execution_time)
                
                # 更新统计
                self._update_stats(True, execution_time)
                
                return ToolResult(
                    call_id=tool_call.call_id or "unknown",
                    success=True,
                    result=result,
                    error=None
                )
                
            except Exception as e:
                last_error = str(e)
                execution_time = time.time() - start_time
                
                self.logger.error(f"❌ 工具执行失败 {tool_call.tool_name} (尝试 {attempt + 1}): {last_error}")
                
                # 记录执行失败
                self._log_execution_failure(tool_call, last_error, execution_time)
                
                # 更新统计
                self._update_stats(False, execution_time)
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.context.max_retry_attempts - 1:
                    self.logger.info(f"⏳ 等待 {self.context.retry_delay} 秒后重试...")
                    await asyncio.sleep(self.context.retry_delay)
                    self.execution_stats['total_retries'] += 1
                else:
                    self.logger.error(f"❌ 工具执行最终失败: {tool_call.tool_name}")
        
        # 所有重试都失败了
        return ToolResult(
            call_id=tool_call.call_id or "unknown",
            success=False,
            result=None,
            error=f"工具执行失败，已重试 {self.context.max_retry_attempts} 次: {last_error}"
        )
    
    async def execute_multiple_tool_calls(self, tool_calls: List[ToolCall], 
                                        parameter_normalizer=None, 
                                        parallel: bool = False) -> List[ToolResult]:
        """执行多个工具调用"""
        if not tool_calls:
            return []
        
        if parallel:
            # 并行执行
            tasks = [
                self.execute_tool_call(tool_call, parameter_normalizer)
                for tool_call in tool_calls
            ]
            return await asyncio.gather(*tasks)
        else:
            # 串行执行
            results = []
            for tool_call in tool_calls:
                result = await self.execute_tool_call(tool_call, parameter_normalizer)
                results.append(result)
            return results
    
    def _log_execution_start(self, tool_call: ToolCall):
        """记录执行开始"""
        if not self.context.enable_logging:
            return
            
        # TaskContext对话记录
        if self.context.task_context and hasattr(self.context.task_context, 'add_conversation_message'):
            self.context.task_context.add_conversation_message(
                role="tool_call",
                content=f"开始调用工具: {tool_call.tool_name}",
                agent_id=self.context.agent_id,
                tool_info={
                    "tool_name": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "status": "started"
                }
            )
        
        # 🆕 记录到TaskContext的工具执行列表
        if self.context.task_context and hasattr(self.context.task_context, 'add_tool_execution'):
            self.context.task_context.add_tool_execution(
                tool_name=tool_call.tool_name,
                parameters=tool_call.parameters,
                agent_id=self.context.agent_id,
                success=False,  # 开始时设为False，成功后会更新
                execution_time=0.0
            )
    
    def _log_execution_success(self, tool_call: ToolCall, result: Any, execution_time: float):
        """记录执行成功"""
        if not self.context.enable_logging:
            return
            
        # 统一日志系统记录
        try:
            from core.unified_logging_system import get_global_logging_system
            logging_system = get_global_logging_system()
            logging_system.log_tool_result(
                agent_id=self.context.agent_id,
                tool_name=tool_call.tool_name,
                success=True,
                result=result,
                duration=execution_time
            )
        except ImportError:
            self.logger.debug("统一日志系统不可用")
        
        # TaskContext对话记录
        if self.context.task_context and hasattr(self.context.task_context, 'add_conversation_message'):
            self.context.task_context.add_conversation_message(
                role="tool_result",
                content=f"工具执行成功: {tool_call.tool_name}",
                agent_id=self.context.agent_id,
                tool_info={
                    "tool_name": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "success": True,
                    "result": str(result)[:200] + ("..." if len(str(result)) > 200 else ""),
                    "status": "completed"
                }
            )
        
        # 🆕 更新TaskContext的工具执行记录
        if self.context.task_context and hasattr(self.context.task_context, 'tool_executions'):
            # 找到最近的工具执行记录并更新
            for tool_exec in reversed(self.context.task_context.tool_executions):
                if (tool_exec.get('tool_name') == tool_call.tool_name and 
                    tool_exec.get('agent_id') == self.context.agent_id and
                    not tool_exec.get('success', True)):  # 找到未成功的记录
                    tool_exec.update({
                        'success': True,
                        'result': str(result)[:500] if result else None,
                        'execution_time': execution_time
                    })
                    break
    
    def _log_execution_failure(self, tool_call: ToolCall, error: str, execution_time: float):
        """记录执行失败"""
        if not self.context.enable_logging:
            return
            
        # 统一日志系统记录
        try:
            from core.unified_logging_system import get_global_logging_system
            logging_system = get_global_logging_system()
            logging_system.log_tool_result(
                agent_id=self.context.agent_id,
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                duration=execution_time,
                error=error
            )
        except ImportError:
            self.logger.debug("统一日志系统不可用")
        
        # TaskContext对话记录
        if self.context.task_context and hasattr(self.context.task_context, 'add_conversation_message'):
            self.context.task_context.add_conversation_message(
                role="tool_error",
                content=f"工具执行失败: {tool_call.tool_name} - {error}",
                agent_id=self.context.agent_id,
                tool_info={
                    "tool_name": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "success": False,
                    "error": error,
                    "status": "failed"
                }
            )
        
        # 🆕 更新TaskContext的工具执行记录
        if self.context.task_context and hasattr(self.context.task_context, 'tool_executions'):
            # 找到最近的工具执行记录并更新
            for tool_exec in reversed(self.context.task_context.tool_executions):
                if (tool_exec.get('tool_name') == tool_call.tool_name and 
                    tool_exec.get('agent_id') == self.context.agent_id and
                    not tool_exec.get('success', True)):  # 找到未成功的记录
                    tool_exec.update({
                        'success': False,
                        'error': error,
                        'execution_time': execution_time
                    })
                    break
    
    def _update_stats(self, success: bool, execution_time: float):
        """更新执行统计"""
        self.execution_stats['total_executions'] += 1
        
        if success:
            self.execution_stats['successful_executions'] += 1
        else:
            self.execution_stats['failed_executions'] += 1
        
        # 更新平均执行时间
        total_time = self.execution_stats['average_execution_time'] * (self.execution_stats['total_executions'] - 1)
        self.execution_stats['average_execution_time'] = (total_time + execution_time) / self.execution_stats['total_executions']
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        stats = self.execution_stats.copy()
        if stats['total_executions'] > 0:
            stats['success_rate'] = stats['successful_executions'] / stats['total_executions']
        else:
            stats['success_rate'] = 0.0
        return stats
    
    def clear_stats(self):
        """清除统计"""
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_retries': 0,
            'average_execution_time': 0.0
        }
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        return self.tool_registry.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """列出所有可用工具"""
        return list(self.tool_registry.keys())
    
    def has_tool(self, tool_name: str) -> bool:
        """检查是否有指定工具"""
        return tool_name in self.tool_registry 