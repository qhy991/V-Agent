"""
🎯 Gradio可视化数据收集器
==================================================

专门为Gradio界面设计的数据收集规范，确保：
- 统一的数据格式
- 完整的执行轨迹
- 清晰的层次结构
- 易于可视化的数据结构
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


class EventType(Enum):
    """事件类型枚举"""
    TASK_START = "task_start"
    TASK_END = "task_end"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    FILE_OPERATION = "file_operation"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AgentType(Enum):
    """智能体类型枚举"""
    COORDINATOR = "coordinator"
    VERILOG_DESIGNER = "verilog_designer"
    CODE_REVIEWER = "code_reviewer"
    TEST_GENERATOR = "test_generator"


@dataclass
class GradioEvent:
    """Gradio事件记录"""
    event_id: str
    event_type: EventType
    timestamp: float
    agent_id: str
    agent_type: AgentType
    session_id: str
    task_id: str
    
    # 事件详情
    title: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    # 性能指标
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    
    # 关联信息
    parent_event_id: Optional[str] = None
    child_event_ids: List[str] = field(default_factory=list)
    
    # 可视化属性
    color: str = "#4CAF50"  # 默认绿色
    icon: str = "✅"
    priority: int = 0  # 0=低, 1=中, 2=高
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    start_time: float
    end_time: Optional[float] = None
    success: bool = True
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    
    @property
    def duration(self) -> float:
        return (self.end_time or time.time()) - self.start_time


@dataclass
class LLMCallRecord:
    """LLM调用记录"""
    conversation_id: str
    user_message: str
    system_prompt: str
    response: str
    start_time: float
    end_time: Optional[float] = None
    token_count: Optional[int] = None
    model_name: str = "unknown"
    
    @property
    def duration(self) -> float:
        return (self.end_time or time.time()) - self.start_time


@dataclass
class AgentSession:
    """智能体会话记录"""
    agent_id: str
    agent_type: AgentType
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    
    # 执行统计
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    llm_calls: List[LLMCallRecord] = field(default_factory=list)
    file_operations: List[Dict[str, Any]] = field(default_factory=list)
    
    # 性能指标
    total_duration: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0
    
    def add_tool_call(self, tool_call: ToolCallRecord):
        self.tool_calls.append(tool_call)
        
    def add_llm_call(self, llm_call: LLMCallRecord):
        self.llm_calls.append(llm_call)
        
    def add_file_operation(self, operation: Dict[str, Any]):
        self.file_operations.append(operation)
        
    def finalize(self):
        """完成会话，计算统计信息"""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time
        
        # 计算成功率
        total_operations = len(self.tool_calls) + len(self.llm_calls)
        if total_operations > 0:
            successful_operations = sum(1 for tc in self.tool_calls if tc.success) + len(self.llm_calls)
            self.success_rate = successful_operations / total_operations
            
        # 计算错误数
        self.error_count = sum(1 for tc in self.tool_calls if not tc.success)


class GradioDataCollector:
    """Gradio数据收集器"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[GradioEvent] = []
        self.agent_sessions: Dict[str, AgentSession] = {}
        self.current_task_id: Optional[str] = None
        self.task_start_time: Optional[float] = None
        
    def start_task(self, task_id: str, task_description: str) -> str:
        """开始任务记录"""
        self.current_task_id = task_id
        self.task_start_time = time.time()
        
        event_id = f"task_{task_id}_{int(time.time())}"
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.TASK_START,
            timestamp=self.task_start_time,
            agent_id="system",
            agent_type=AgentType.COORDINATOR,
            session_id=self.session_id,
            task_id=task_id,
            title="任务开始",
            description=task_description,
            details={"task_description": task_description},
            color="#2196F3",
            icon="🚀",
            priority=2
        )
        
        self.events.append(event)
        return event_id
        
    def end_task(self, task_id: str, success: bool = True, summary: str = "") -> str:
        """结束任务记录"""
        if not self.task_start_time:
            return ""
            
        event_id = f"task_end_{task_id}_{int(time.time())}"
        duration = time.time() - self.task_start_time
        
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.TASK_END,
            timestamp=time.time(),
            agent_id="system",
            agent_type=AgentType.COORDINATOR,
            session_id=self.session_id,
            task_id=task_id,
            title="任务完成" if success else "任务失败",
            description=summary,
            details={
                "duration": duration,
                "success": success,
                "summary": summary
            },
            duration=duration,
            success=success,
            color="#4CAF50" if success else "#F44336",
            icon="✅" if success else "❌",
            priority=2
        )
        
        self.events.append(event)
        return event_id
        
    def start_agent_session(self, agent_id: str, agent_type: AgentType, task_id: str) -> str:
        """开始智能体会话"""
        session_id = f"{agent_id}_{int(time.time())}"
        
        session = AgentSession(
            agent_id=agent_id,
            agent_type=agent_type,
            session_id=session_id,
            start_time=time.time()
        )
        
        self.agent_sessions[session_id] = session
        
        # 创建事件记录
        event_id = f"agent_start_{session_id}"
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.AGENT_START,
            timestamp=session.start_time,
            agent_id=agent_id,
            agent_type=agent_type,
            session_id=self.session_id,
            task_id=task_id,
            title=f"{agent_id} 开始工作",
            description=f"智能体 {agent_id} 开始执行任务",
            details={"session_id": session_id},
            color="#FF9800",
            icon="🤖",
            priority=1
        )
        
        self.events.append(event)
        return session_id
        
    def end_agent_session(self, session_id: str, success: bool = True) -> str:
        """结束智能体会话"""
        if session_id not in self.agent_sessions:
            return ""
            
        session = self.agent_sessions[session_id]
        session.finalize()
        
        # 创建事件记录
        event_id = f"agent_end_{session_id}"
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.AGENT_END,
            timestamp=time.time(),
            agent_id=session.agent_id,
            agent_type=session.agent_type,
            session_id=self.session_id,
            task_id=self.current_task_id or "unknown",
            title=f"{session.agent_id} 完成工作",
            description=f"执行时间: {session.total_duration:.2f}秒, 成功率: {session.success_rate:.1%}",
            details={
                "duration": session.total_duration,
                "success_rate": session.success_rate,
                "tool_calls": len(session.tool_calls),
                "llm_calls": len(session.llm_calls),
                "file_operations": len(session.file_operations)
            },
            duration=session.total_duration,
            success=success,
            color="#4CAF50" if success else "#F44336",
            icon="✅" if success else "❌",
            priority=1
        )
        
        self.events.append(event)
        return event_id
        
    def record_tool_call(self, session_id: str, tool_name: str, parameters: Dict[str, Any]) -> str:
        """记录工具调用"""
        if session_id not in self.agent_sessions:
            return ""
            
        session = self.agent_sessions[session_id]
        tool_call = ToolCallRecord(
            tool_name=tool_name,
            parameters=parameters,
            start_time=time.time()
        )
        
        session.add_tool_call(tool_call)
        
        # 创建事件记录
        event_id = f"tool_call_{session_id}_{len(session.tool_calls)}"
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.TOOL_CALL,
            timestamp=tool_call.start_time,
            agent_id=session.agent_id,
            agent_type=session.agent_type,
            session_id=self.session_id,
            task_id=self.current_task_id or "unknown",
            title=f"调用工具: {tool_name}",
            description=f"参数: {json.dumps(parameters, ensure_ascii=False)[:100]}...",
            details={
                "tool_name": tool_name,
                "parameters": parameters,
                "session_id": session_id
            },
            color="#9C27B0",
            icon="🔧",
            priority=0
        )
        
        self.events.append(event)
        return event_id
        
    def record_tool_result(self, session_id: str, tool_name: str, success: bool, 
                          result: Any = None, error: str = None) -> str:
        """记录工具执行结果"""
        if session_id not in self.agent_sessions:
            return ""
            
        session = self.agent_sessions[session_id]
        
        # 找到对应的工具调用
        for tool_call in session.tool_calls:
            if tool_call.tool_name == tool_name and tool_call.end_time is None:
                tool_call.end_time = time.time()
                tool_call.success = success
                tool_call.result = result
                tool_call.error = error
                break
        
        # 创建事件记录
        event_id = f"tool_result_{session_id}_{tool_name}_{int(time.time())}"
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.TOOL_RESULT,
            timestamp=time.time(),
            agent_id=session.agent_id,
            agent_type=session.agent_type,
            session_id=self.session_id,
            task_id=self.current_task_id or "unknown",
            title=f"工具执行: {tool_name}",
            description=f"{'成功' if success else '失败'}: {str(result)[:100] if result else error}",
            details={
                "tool_name": tool_name,
                "success": success,
                "result": str(result)[:200] if result else None,
                "error": error,
                "session_id": session_id
            },
            success=success,
            color="#4CAF50" if success else "#F44336",
            icon="✅" if success else "❌",
            priority=0
        )
        
        self.events.append(event)
        return event_id
        
    def record_llm_call(self, session_id: str, user_message: str, system_prompt: str, 
                       response: str, model_name: str = "unknown") -> str:
        """记录LLM调用"""
        if session_id not in self.agent_sessions:
            return ""
            
        session = self.agent_sessions[session_id]
        llm_call = LLMCallRecord(
            conversation_id=f"{session_id}_{len(session.llm_calls)}",
            user_message=user_message,
            system_prompt=system_prompt,
            response=response,
            start_time=time.time(),
            model_name=model_name
        )
        
        session.add_llm_call(llm_call)
        
        # 创建事件记录
        event_id = f"llm_call_{session_id}_{len(session.llm_calls)}"
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.LLM_CALL,
            timestamp=llm_call.start_time,
            agent_id=session.agent_id,
            agent_type=session.agent_type,
            session_id=self.session_id,
            task_id=self.current_task_id or "unknown",
            title=f"LLM调用 ({model_name})",
            description=f"用户消息: {user_message[:100]}...",
            details={
                "model_name": model_name,
                "user_message_length": len(user_message),
                "response_length": len(response),
                "session_id": session_id
            },
            color="#2196F3",
            icon="🧠",
            priority=0
        )
        
        self.events.append(event)
        return event_id
        
    def record_file_operation(self, session_id: str, operation: str, file_path: str, 
                             success: bool, details: str = "") -> str:
        """记录文件操作"""
        if session_id not in self.agent_sessions:
            return ""
            
        session = self.agent_sessions[session_id]
        
        file_op = {
            "operation": operation,
            "file_path": file_path,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        
        session.add_file_operation(file_op)
        
        # 创建事件记录
        event_id = f"file_op_{session_id}_{int(time.time())}"
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.FILE_OPERATION,
            timestamp=file_op["timestamp"],
            agent_id=session.agent_id,
            agent_type=session.agent_type,
            session_id=self.session_id,
            task_id=self.current_task_id or "unknown",
            title=f"文件操作: {operation}",
            description=f"文件: {file_path}",
            details=file_op,
            success=success,
            color="#FF9800" if success else "#F44336",
            icon="📁" if success else "❌",
            priority=0
        )
        
        self.events.append(event)
        return event_id
        
    def record_error(self, session_id: str, error_message: str, error_type: str = "error") -> str:
        """记录错误"""
        event_id = f"error_{session_id}_{int(time.time())}"
        
        agent_id = "system"
        agent_type = AgentType.COORDINATOR
        
        if session_id in self.agent_sessions:
            agent_id = self.agent_sessions[session_id].agent_id
            agent_type = self.agent_sessions[session_id].agent_type
        
        event = GradioEvent(
            event_id=event_id,
            event_type=EventType.ERROR,
            timestamp=time.time(),
            agent_id=agent_id,
            agent_type=agent_type,
            session_id=self.session_id,
            task_id=self.current_task_id or "unknown",
            title=f"错误: {error_type}",
            description=error_message,
            details={
                "error_message": error_message,
                "error_type": error_type,
                "session_id": session_id
            },
            success=False,
            error_message=error_message,
            color="#F44336",
            icon="❌",
            priority=1
        )
        
        self.events.append(event)
        return event_id
        
    def get_execution_timeline(self) -> List[Dict[str, Any]]:
        """获取执行时间线"""
        timeline = []
        
        for event in sorted(self.events, key=lambda x: x.timestamp):
            timeline.append({
                "timestamp": event.timestamp,
                "event_type": event.event_type.value,
                "agent_id": event.agent_id,
                "title": event.title,
                "description": event.description,
                "color": event.color,
                "icon": event.icon,
                "success": event.success,
                "duration": event.duration,
                "details": event.details
            })
            
        return timeline
        
    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """获取智能体性能摘要"""
        summary = {}
        
        for session_id, session in self.agent_sessions.items():
            summary[session.agent_id] = {
                "agent_type": session.agent_type.value,
                "total_duration": session.total_duration,
                "success_rate": session.success_rate,
                "tool_calls": len(session.tool_calls),
                "llm_calls": len(session.llm_calls),
                "file_operations": len(session.file_operations),
                "error_count": session.error_count
            }
            
        return summary
        
    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务摘要"""
        if not self.task_start_time:
            return {}
            
        total_duration = time.time() - self.task_start_time
        
        return {
            "task_id": self.current_task_id,
            "session_id": self.session_id,
            "start_time": self.task_start_time,
            "total_duration": total_duration,
            "total_events": len(self.events),
            "agent_sessions": len(self.agent_sessions),
            "success_rate": sum(1 for e in self.events if e.success) / max(len(self.events), 1)
        }
        
    def export_data(self) -> Dict[str, Any]:
        """导出所有数据"""
        return {
            "session_id": self.session_id,
            "task_summary": self.get_task_summary(),
            "agent_performance": self.get_agent_performance_summary(),
            "execution_timeline": self.get_execution_timeline(),
            "events": [event.to_dict() for event in self.events],
            "agent_sessions": {
                session_id: {
                    "agent_id": session.agent_id,
                    "agent_type": session.agent_type.value,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "total_duration": session.total_duration,
                    "success_rate": session.success_rate,
                    "tool_calls": [
                        {
                            "tool_name": tc.tool_name,
                            "parameters": tc.parameters,
                            "duration": tc.duration,
                            "success": tc.success,
                            "result": str(tc.result)[:200] if tc.result else None,
                            "error": tc.error
                        } for tc in session.tool_calls
                    ],
                    "llm_calls": [
                        {
                            "conversation_id": lc.conversation_id,
                            "model_name": lc.model_name,
                            "duration": lc.duration,
                            "user_message_length": len(lc.user_message),
                            "response_length": len(lc.response)
                        } for lc in session.llm_calls
                    ],
                    "file_operations": session.file_operations
                } for session_id, session in self.agent_sessions.items()
            }
        }


# 全局数据收集器实例
_global_collector: Optional[GradioDataCollector] = None


def get_global_collector() -> GradioDataCollector:
    """获取全局数据收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = GradioDataCollector(f"session_{int(time.time())}")
    return _global_collector


def set_global_collector(collector: GradioDataCollector):
    """设置全局数据收集器"""
    global _global_collector
    _global_collector = collector 