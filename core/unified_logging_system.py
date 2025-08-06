"""
🎯 统一日志记录系统
==================================================

规范化所有agent的工具调用和对话记录，确保：
- 统一的数据格式
- 完整的执行轨迹
- 清晰的层次结构
- 易于可视化的数据结构
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class EventCategory(Enum):
    """事件类别"""
    TASK = "task"
    AGENT = "agent"
    TOOL = "tool"
    LLM = "llm"
    FILE = "file"
    SYSTEM = "system"


@dataclass
class UnifiedLogEvent:
    """统一日志事件"""
    # 基础信息
    event_id: str
    timestamp: float
    level: LogLevel
    category: EventCategory
    
    # 上下文信息
    session_id: str
    task_id: str
    agent_id: str
    title: str
    message: str
    
    # 可选上下文信息
    conversation_id: Optional[str] = None
    
    # 事件内容
    details: Dict[str, Any] = field(default_factory=dict)
    
    # 性能指标
    duration: Optional[float] = None
    success: bool = True
    error_info: Optional[Dict[str, Any]] = None
    
    # 关联信息
    parent_event_id: Optional[str] = None
    related_event_ids: List[str] = field(default_factory=list)
    
    # 可视化属性
    color: str = "#4CAF50"
    icon: str = "✅"
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UnifiedLoggingSystem:
    """统一日志记录系统"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[UnifiedLogEvent] = []
        self.current_task_id: Optional[str] = None
        self.task_start_time: Optional[float] = None
        
        # 设置日志记录器
        self.logger = logging.getLogger(f"UnifiedLogging_{session_id}")
        self.logger.setLevel(logging.DEBUG)
        
    def _generate_event_id(self, prefix: str) -> str:
        """生成事件ID"""
        return f"{prefix}_{int(time.time() * 1000)}"
        
    def log_event(self, level: LogLevel, category: EventCategory, title: str, 
                  message: str, agent_id: str, details: Dict[str, Any] = None,
                  success: bool = True, duration: Optional[float] = None,
                  error_info: Optional[Dict[str, Any]] = None,
                  parent_event_id: Optional[str] = None) -> str:
        """记录统一事件"""
        
        event_id = self._generate_event_id(category.value)
        
        event = UnifiedLogEvent(
            event_id=event_id,
            timestamp=time.time(),
            level=level,
            category=category,
            session_id=self.session_id,
            task_id=self.current_task_id or "unknown",
            agent_id=agent_id,
            title=title,
            message=message,
            details=details or {},
            duration=duration,
            success=success,
            error_info=error_info,
            parent_event_id=parent_event_id
        )
        
        # 设置可视化属性
        if not success:
            event.color = "#F44336"
            event.icon = "❌"
        elif level == LogLevel.WARNING:
            event.color = "#FF9800"
            event.icon = "⚠️"
        elif level == LogLevel.ERROR:
            event.color = "#F44336"
            event.icon = "🚨"
            
        self.events.append(event)
        
        # 同时记录到标准日志
        log_message = f"[{event_id}] {title}: {message}"
        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
            
        return event_id
        
    def start_task(self, task_id: str, task_description: str) -> str:
        """开始任务记录"""
        self.current_task_id = task_id
        self.task_start_time = time.time()
        
        return self.log_event(
            level=LogLevel.INFO,
            category=EventCategory.TASK,
            title="任务开始",
            message=task_description,
            agent_id="system",
            details={"task_description": task_description}
        )
        
    def end_task(self, success: bool = True, summary: str = "") -> str:
        """结束任务记录"""
        if not self.task_start_time:
            return ""
            
        duration = time.time() - self.task_start_time
        
        return self.log_event(
            level=LogLevel.INFO,
            category=EventCategory.TASK,
            title="任务完成" if success else "任务失败",
            message=summary,
            agent_id="system",
            details={
                "duration": duration,
                "success": success,
                "summary": summary
            },
            duration=duration,
            success=success
        )
        
    def log_agent_start(self, agent_id: str, task_description: str) -> str:
        """记录智能体开始"""
        return self.log_event(
            level=LogLevel.INFO,
            category=EventCategory.AGENT,
            title=f"{agent_id} 开始工作",
            message=task_description,
            agent_id=agent_id,
            details={"task_description": task_description}
        )
        
    def log_agent_end(self, agent_id: str, success: bool = True, 
                     summary: str = "", duration: Optional[float] = None) -> str:
        """记录智能体结束"""
        return self.log_event(
            level=LogLevel.INFO,
            category=EventCategory.AGENT,
            title=f"{agent_id} 完成工作",
            message=summary,
            agent_id=agent_id,
            details={"duration": duration, "summary": summary},
            duration=duration,
            success=success
        )
        
    def log_tool_call(self, agent_id: str, tool_name: str, 
                     parameters: Dict[str, Any], start_time: float) -> str:
        """记录工具调用"""
        return self.log_event(
            level=LogLevel.INFO,
            category=EventCategory.TOOL,
            title=f"调用工具: {tool_name}",
            message=f"参数: {json.dumps(parameters, ensure_ascii=False)[:100]}...",
            agent_id=agent_id,
            details={
                "tool_name": tool_name,
                "parameters": parameters,
                "start_time": start_time
            }
        )
        
    def log_tool_result(self, agent_id: str, tool_name: str, 
                       success: bool, result: Any = None, 
                       error: str = None, duration: Optional[float] = None) -> str:
        """记录工具执行结果"""
        message = f"{'成功' if success else '失败'}: {str(result)[:100] if result else error}"
        
        return self.log_event(
            level=LogLevel.INFO if success else LogLevel.ERROR,
            category=EventCategory.TOOL,
            title=f"工具执行: {tool_name}",
            message=message,
            agent_id=agent_id,
            details={
                "tool_name": tool_name,
                "success": success,
                "result": str(result)[:200] if result else None,
                "error": error,
                "duration": duration
            },
            duration=duration,
            success=success
        )
        
    def log_llm_call(self, agent_id: str, model_name: str, 
                    user_message: str, response: str, 
                    duration: Optional[float] = None) -> str:
        """记录LLM调用"""
        return self.log_event(
            level=LogLevel.INFO,
            category=EventCategory.LLM,
            title=f"LLM调用 ({model_name})",
            message=f"用户消息: {user_message[:100]}...",
            agent_id=agent_id,
            details={
                "model_name": model_name,
                "user_message_length": len(user_message),
                "response_length": len(response),
                "duration": duration
            },
            duration=duration
        )
        
    def log_file_operation(self, agent_id: str, operation: str, 
                          file_path: str, success: bool, 
                          details: str = "") -> str:
        """记录文件操作"""
        return self.log_event(
            level=LogLevel.INFO if success else LogLevel.ERROR,
            category=EventCategory.FILE,
            title=f"文件操作: {operation}",
            message=f"文件: {file_path}",
            agent_id=agent_id,
            details={
                "operation": operation,
                "file_path": file_path,
                "success": success,
                "details": details
            },
            success=success
        )
        
    def log_error(self, agent_id: str, error_message: str, 
                 error_type: str = "error", details: Dict[str, Any] = None) -> str:
        """记录错误"""
        return self.log_event(
            level=LogLevel.ERROR,
            category=EventCategory.SYSTEM,
            title=f"错误: {error_type}",
            message=error_message,
            agent_id=agent_id,
            details=details or {},
            success=False,
            error_info={"error_type": error_type, "error_message": error_message}
        )
        
    def log_warning(self, agent_id: str, warning_message: str, 
                   details: Dict[str, Any] = None) -> str:
        """记录警告"""
        return self.log_event(
            level=LogLevel.WARNING,
            category=EventCategory.SYSTEM,
            title="警告",
            message=warning_message,
            agent_id=agent_id,
            details=details or {}
        )
        
    def get_execution_timeline(self) -> List[Dict[str, Any]]:
        """获取执行时间线"""
        timeline = []
        
        for event in sorted(self.events, key=lambda x: x.timestamp):
            timeline.append({
                "timestamp": event.timestamp,
                "event_id": event.event_id,
                "category": event.category.value,
                "level": event.level.value,
                "agent_id": event.agent_id,
                "title": event.title,
                "message": event.message,
                "color": event.color,
                "icon": event.icon,
                "success": event.success,
                "duration": event.duration,
                "details": event.details,
                "priority": event.priority
            })
            
        return timeline
        
    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """获取智能体性能摘要"""
        agent_stats = {}
        
        for event in self.events:
            if event.category == EventCategory.AGENT:
                agent_id = event.agent_id
                if agent_id not in agent_stats:
                    agent_stats[agent_id] = {
                        "start_events": 0,
                        "end_events": 0,
                        "total_duration": 0.0,
                        "success_count": 0,
                        "error_count": 0
                    }
                    
                if "开始工作" in event.title:
                    agent_stats[agent_id]["start_events"] += 1
                elif "完成工作" in event.title:
                    agent_stats[agent_id]["end_events"] += 1
                    if event.success:
                        agent_stats[agent_id]["success_count"] += 1
                    else:
                        agent_stats[agent_id]["error_count"] += 1
                    if event.duration:
                        agent_stats[agent_id]["total_duration"] += event.duration
                        
        return agent_stats
        
    def get_tool_usage_summary(self) -> Dict[str, Any]:
        """获取工具使用摘要"""
        tool_stats = {}
        
        for event in self.events:
            if event.category == EventCategory.TOOL:
                tool_name = event.details.get("tool_name", "unknown")
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {
                        "call_count": 0,
                        "success_count": 0,
                        "error_count": 0,
                        "total_duration": 0.0,
                        "avg_duration": 0.0
                    }
                    
                tool_stats[tool_name]["call_count"] += 1
                if event.success:
                    tool_stats[tool_name]["success_count"] += 1
                else:
                    tool_stats[tool_name]["error_count"] += 1
                    
                if event.duration:
                    tool_stats[tool_name]["total_duration"] += event.duration
                    
        # 计算平均持续时间
        for tool_name, stats in tool_stats.items():
            if stats["call_count"] > 0:
                stats["avg_duration"] = stats["total_duration"] / stats["call_count"]
                
        return tool_stats
        
    def export_data(self) -> Dict[str, Any]:
        """导出所有数据"""
        return {
            "session_id": self.session_id,
            "task_id": self.current_task_id,
            "task_duration": time.time() - self.task_start_time if self.task_start_time else 0,
            "total_events": len(self.events),
            "execution_timeline": self.get_execution_timeline(),
            "agent_performance": self.get_agent_performance_summary(),
            "tool_usage": self.get_tool_usage_summary(),
            "events": [event.to_dict() for event in self.events]
        }


# 全局日志系统实例
_global_logging_system: Optional[UnifiedLoggingSystem] = None


def get_global_logging_system() -> UnifiedLoggingSystem:
    """获取全局日志系统"""
    global _global_logging_system
    if _global_logging_system is None:
        _global_logging_system = UnifiedLoggingSystem(f"session_{int(time.time())}")
    return _global_logging_system


def set_global_logging_system(system: UnifiedLoggingSystem):
    """设置全局日志系统"""
    global _global_logging_system
    _global_logging_system = system 