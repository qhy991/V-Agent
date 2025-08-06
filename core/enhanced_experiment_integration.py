"""
增强实验记录集成模块 - 将增强实验记录器集成到现有系统中
"""

import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from .enhanced_experiment_recorder import (
    EnhancedExperimentRecorder, 
    MessageType, 
    AgentType,
    ToolCallRecord
)
from .llm_coordinator_agent import LLMCoordinatorAgent, TaskContext
from .schema_system.enhanced_base_agent import EnhancedBaseAgent


class EnhancedExperimentIntegration:
    """增强实验记录集成器"""
    
    def __init__(self, experiment_id: str, output_dir: Path):
        self.experiment_id = experiment_id
        self.output_dir = output_dir
        self.recorder = EnhancedExperimentRecorder(experiment_id, output_dir)
        self.logger = self.recorder.logger
        
        # 记录器状态
        self.is_recording = False
        self.current_coordinator = None
        self.agent_wrappers = {}
    
    def start_recording(self, original_request: str):
        """开始记录实验"""
        self.recorder.set_original_request(original_request)
        self.is_recording = True
        self.logger.info(f"🎬 开始记录实验: {self.experiment_id}")
    
    def stop_recording(self, success: bool = True, error_message: str = None):
        """停止记录实验"""
        self.is_recording = False
        self.recorder.complete_experiment(success, error_message)
        self.logger.info(f"⏹️ 停止记录实验: {self.experiment_id}")
    
    def save_report(self) -> Dict[str, Any]:
        """保存实验报告"""
        return self.recorder.save_experiment_report()
    
    def wrap_coordinator(self, coordinator: LLMCoordinatorAgent) -> 'EnhancedCoordinatorWrapper':
        """包装协调智能体以记录其活动"""
        if not self.is_recording:
            raise RuntimeError("实验记录器未启动")
        
        wrapper = EnhancedCoordinatorWrapper(coordinator, self.recorder)
        self.current_coordinator = wrapper
        return wrapper
    
    def wrap_agent(self, agent: EnhancedBaseAgent) -> 'EnhancedAgentWrapper':
        """包装智能体以记录其活动"""
        if not self.is_recording:
            raise RuntimeError("实验记录器未启动")
        
        wrapper = EnhancedAgentWrapper(agent, self.recorder)
        self.agent_wrappers[agent.agent_id] = wrapper
        return wrapper
    
    def record_user_message(self, content: str, metadata: Dict[str, Any] = None):
        """记录用户消息"""
        if self.is_recording:
            self.recorder.add_user_message(content, metadata)
    
    def record_system_message(self, content: str, metadata: Dict[str, Any] = None):
        """记录系统消息"""
        if self.is_recording:
            self.recorder.add_system_message(content, metadata)
    
    def record_tool_call(self, agent_id: str, tool_name: str, parameters: Dict[str, Any],
                        success: bool = True, result: Dict[str, Any] = None,
                        error_message: str = None, execution_time: float = 0.0):
        """记录工具调用"""
        if self.is_recording:
            self.recorder.add_tool_call(
                agent_id, tool_name, parameters, success, result, 
                error_message, execution_time
            )
    
    def record_file_operation(self, operation_type: str, file_path: str, 
                            agent_id: str, success: bool = True):
        """记录文件操作"""
        if self.is_recording:
            self.recorder.record_file_operation(operation_type, file_path, agent_id, success)
    
    def record_error(self, agent_id: str, error_message: str, metadata: Dict[str, Any] = None):
        """记录错误"""
        if self.is_recording:
            self.recorder.add_error_message(agent_id, error_message, metadata)
    
    def record_info(self, agent_id: str, info_message: str, metadata: Dict[str, Any] = None):
        """记录信息"""
        if self.is_recording:
            self.recorder.add_info_message(agent_id, info_message, metadata)


class EnhancedCoordinatorWrapper:
    """增强协调智能体包装器"""
    
    def __init__(self, coordinator: LLMCoordinatorAgent, recorder: EnhancedExperimentRecorder):
        self.coordinator = coordinator
        self.recorder = recorder
        self.logger = recorder.logger
        
        # 开始协调智能体会话
        self.recorder.start_agent_session(
            coordinator.agent_id, 
            AgentType.COORDINATOR
        )
        
        # 记录协调智能体初始化
        self.recorder.add_info_message(
            coordinator.agent_id,
            f"协调智能体 {coordinator.agent_id} 已初始化",
            {"capabilities": list(coordinator.get_capabilities())}
        )
    
    async def coordinate_task(self, user_request: str, **kwargs) -> Dict[str, Any]:
        """协调任务 - 增强版本"""
        start_time = time.time()
        
        try:
            # 记录用户请求
            self.recorder.add_user_message(user_request)
            
            # 记录协调开始
            self.recorder.add_info_message(
                self.coordinator.agent_id,
                f"开始协调任务: {user_request[:100]}...",
                {"request_length": len(user_request)}
            )
            
            # 执行原始协调任务
            result = await self.coordinator.coordinate_task(user_request, **kwargs)
            
            # 记录协调结果
            execution_time = time.time() - start_time
            success = result.get('success', False)
            
            self.recorder.add_assistant_message(
                self.coordinator.agent_id,
                f"协调任务完成，耗时: {execution_time:.2f}秒",
                {
                    "success": success,
                    "execution_time": execution_time,
                    "agent_results": list(result.get('agent_results', {}).keys()),
                    "total_iterations": result.get('execution_summary', {}).get('total_iterations', 0)
                }
            )
            
            # 记录文件操作
            if success:
                generated_files = result.get('generated_files', [])
                for file_path in generated_files:
                    self.recorder.record_file_operation("generate", file_path, self.coordinator.agent_id)
            
            return result
            
        except Exception as e:
            # 记录错误
            execution_time = time.time() - start_time
            error_msg = f"协调任务失败: {str(e)}"
            self.recorder.record_error(self.coordinator.agent_id, error_msg, {
                "execution_time": execution_time,
                "error_type": type(e).__name__
            })
            raise
    
    def __getattr__(self, name):
        """代理其他属性到原始协调智能体"""
        return getattr(self.coordinator, name)


class EnhancedAgentWrapper:
    """增强智能体包装器"""
    
    def __init__(self, agent: EnhancedBaseAgent, recorder: EnhancedExperimentRecorder):
        self.agent = agent
        self.recorder = recorder
        self.logger = recorder.logger
        
        # 确定智能体类型
        agent_type = self._determine_agent_type(agent.agent_id)
        
        # 开始智能体会话
        self.recorder.start_agent_session(agent.agent_id, agent_type)
        
        # 记录智能体初始化
        self.recorder.add_info_message(
            agent.agent_id,
            f"智能体 {agent.agent_id} 已初始化",
            {
                "capabilities": list(agent.get_capabilities()),
                "specialty": agent.get_specialty_description()
            }
        )
    
    async def execute_enhanced_task(self, enhanced_prompt: str, 
                                  original_message: Any, 
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行增强任务 - 增强版本"""
        start_time = time.time()
        
        try:
            # 记录任务开始
            self.recorder.add_info_message(
                self.agent.agent_id,
                f"开始执行任务: {enhanced_prompt[:100]}...",
                {"prompt_length": len(enhanced_prompt)}
            )
            
            # 执行原始任务
            result = await self.agent.execute_enhanced_task(
                enhanced_prompt, original_message, file_contents
            )
            
            # 记录任务结果
            execution_time = time.time() - start_time
            success = result.get('success', False)
            
            self.recorder.add_assistant_message(
                self.agent.agent_id,
                f"任务执行完成，耗时: {execution_time:.2f}秒",
                {
                    "success": success,
                    "execution_time": execution_time,
                    "result_length": len(str(result.get('content', '')))
                }
            )
            
            # 记录文件操作
            if success and 'file_path' in result:
                self.recorder.record_file_operation("generate", result['file_path'], self.agent.agent_id)
            
            return result
            
        except Exception as e:
            # 记录错误
            execution_time = time.time() - start_time
            error_msg = f"任务执行失败: {str(e)}"
            self.recorder.record_error(self.agent.agent_id, error_msg, {
                "execution_time": execution_time,
                "error_type": type(e).__name__
            })
            raise
    
    async def process_with_function_calling(self, user_request: str, **kwargs) -> str:
        """处理函数调用 - 增强版本"""
        start_time = time.time()
        
        try:
            # 记录用户请求
            self.recorder.add_user_message(user_request)
            
            # 记录处理开始
            self.recorder.add_info_message(
                self.agent.agent_id,
                f"开始处理函数调用: {user_request[:100]}...",
                {"request_length": len(user_request)}
            )
            
            # 执行原始处理
            result = await self.agent.process_with_function_calling(user_request, **kwargs)
            
            # 记录处理结果
            execution_time = time.time() - start_time
            
            self.recorder.add_assistant_message(
                self.agent.agent_id,
                f"函数调用处理完成，耗时: {execution_time:.2f}秒",
                {
                    "execution_time": execution_time,
                    "result_length": len(result)
                }
            )
            
            return result
            
        except Exception as e:
            # 记录错误
            execution_time = time.time() - start_time
            error_msg = f"函数调用处理失败: {str(e)}"
            self.recorder.record_error(self.agent.agent_id, error_msg, {
                "execution_time": execution_time,
                "error_type": type(e).__name__
            })
            raise
    
    def _determine_agent_type(self, agent_id: str) -> AgentType:
        """确定智能体类型"""
        if "verilog" in agent_id.lower():
            return AgentType.VERILOG_AGENT
        elif "review" in agent_id.lower():
            return AgentType.CODE_REVIEW_AGENT
        elif "coordinator" in agent_id.lower():
            return AgentType.COORDINATOR
        else:
            return AgentType.COORDINATOR  # 默认类型
    
    def __getattr__(self, name):
        """代理其他属性到原始智能体"""
        return getattr(self.agent, name)


class ExperimentContextManager:
    """实验上下文管理器"""
    
    def __init__(self, experiment_id: str, output_dir: Path):
        self.experiment_id = experiment_id
        self.output_dir = output_dir
        self.integration = None
    
    @asynccontextmanager
    async def experiment_context(self, original_request: str):
        """实验上下文管理器"""
        try:
            # 创建集成器
            self.integration = EnhancedExperimentIntegration(
                self.experiment_id, 
                self.output_dir
            )
            
            # 开始记录
            self.integration.start_recording(original_request)
            
            yield self.integration
            
        except Exception as e:
            # 记录错误并停止记录
            if self.integration:
                self.integration.stop_recording(False, str(e))
            raise
        finally:
            # 确保停止记录
            if self.integration and self.integration.is_recording:
                self.integration.stop_recording(True)
    
    def get_integration(self) -> Optional[EnhancedExperimentIntegration]:
        """获取当前集成器"""
        return self.integration


# 工具函数
def create_experiment_recorder(experiment_id: str, output_dir: Path) -> EnhancedExperimentIntegration:
    """创建实验记录器"""
    return EnhancedExperimentIntegration(experiment_id, output_dir)


def wrap_coordinator_for_recording(coordinator: LLMCoordinatorAgent, 
                                 recorder: EnhancedExperimentRecorder) -> EnhancedCoordinatorWrapper:
    """包装协调智能体用于记录"""
    return EnhancedCoordinatorWrapper(coordinator, recorder)


def wrap_agent_for_recording(agent: EnhancedBaseAgent, 
                           recorder: EnhancedExperimentRecorder) -> EnhancedAgentWrapper:
    """包装智能体用于记录"""
    return EnhancedAgentWrapper(agent, recorder)


# 装饰器
def record_experiment(experiment_id: str, output_dir: Path):
    """实验记录装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 创建实验上下文管理器
            context_manager = ExperimentContextManager(experiment_id, output_dir)
            
            # 获取原始请求（假设是第一个参数）
            original_request = args[0] if args else kwargs.get('user_request', '')
            
            async with context_manager.experiment_context(original_request) as integration:
                # 将集成器添加到kwargs中
                kwargs['experiment_recorder'] = integration
                
                # 执行原始函数
                result = await func(*args, **kwargs)
                
                # 保存报告
                integration.save_report()
                
                return result
        
        return wrapper
    return decorator 