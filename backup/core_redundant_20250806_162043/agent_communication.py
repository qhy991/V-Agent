#!/usr/bin/env python3
"""
智能体间标准化通信格式

Standardized Agent Communication Protocol
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import json
import time
from pathlib import Path


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 待处理
    IN_PROGRESS = "in_progress"   # 进行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    BLOCKED = "blocked"          # 阻塞
    CANCELLED = "cancelled"      # 取消


class MessageType(Enum):
    """消息类型枚举"""
    TASK_ASSIGNMENT = "task_assignment"      # 任务分配
    TASK_RESULT = "task_result"             # 任务结果
    TASK_UPDATE = "task_update"             # 任务更新
    AGENT_QUERY = "agent_query"             # 智能体查询
    AGENT_RESPONSE = "agent_response"        # 智能体响应
    COORDINATION_REQUEST = "coordination_request"  # 协调请求
    COORDINATION_RESPONSE = "coordination_response" # 协调响应


class AgentCapabilityType(Enum):
    """智能体能力类型"""
    VERILOG_DESIGN = "verilog_design"
    CODE_REVIEW = "code_review"
    TEST_GENERATION = "test_generation"
    SIMULATION = "simulation"
    DOCUMENTATION = "documentation"
    OPTIMIZATION = "optimization"


@dataclass
class AgentInfo:
    """智能体信息"""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    current_status: str
    current_workload: int  # 0-100
    success_rate: float   # 0.0-1.0
    average_response_time: float  # seconds


@dataclass
class TaskRequirement:
    """任务需求定义"""
    task_id: str
    task_type: str
    priority: int  # 1-10, 10为最高优先级
    description: str
    requirements: Dict[str, Any]
    dependencies: List[str]  # 依赖的其他任务ID
    expected_outputs: List[str]
    deadline: Optional[float] = None  # timestamp
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class TaskResult:
    """任务结果 - 增强的完成报告"""
    task_id: str
    agent_id: str
    status: TaskStatus
    result_data: Dict[str, Any]
    generated_files: List[str]
    execution_time: float
    quality_metrics: Dict[str, float]
    error_message: Optional[str] = None
    next_steps: Optional[List[str]] = None
    
    # 增强的报告字段
    summary: Optional[str] = None
    detailed_report: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.detailed_report is None:
            self.detailed_report = {}
    
    def get_standardized_report(self) -> Dict[str, Any]:
        """获取标准化的任务完成报告"""
        return {
            "task_summary": {
                "task_id": self.task_id,
                "agent_id": self.agent_id,
                "status": self.status.value,
                "execution_time_seconds": round(self.execution_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "summary": self.summary or f"{self.agent_id} 完成任务 {self.task_id}"
            },
            "generated_artifacts": {
                "files": [
                    {
                        "path": file_path,
                        "type": self._get_file_type(file_path),
                        "size_bytes": self._get_file_size(file_path),
                        "description": self._get_file_description(file_path)
                    }
                    for file_path in self.generated_files
                ],
                "total_files": len(self.generated_files)
            },
            "execution_details": {
                "status": self.status.value,
                "quality_metrics": self.quality_metrics,
                "performance_metrics": {
                    "execution_time_seconds": round(self.execution_time, 2),
                    "files_per_second": round(len(self.generated_files) / max(self.execution_time, 0.1), 2)
                }
            },
            "technical_details": {
                "result_data": self.result_data,
                "detailed_report": self.detailed_report
            },
            "issues_and_recommendations": {
                "errors": self.error_message,
                "next_steps": self.next_steps or [],
                "warnings": self.detailed_report.get("warnings", []),
                "improvements": self.detailed_report.get("improvements", [])
            }
        }
    
    def _get_file_type(self, file_path: str) -> str:
        """获取文件类型"""
        suffix = Path(file_path).suffix.lower()
        type_map = {
            '.v': 'verilog_source',
            '.sv': 'systemverilog_source',
            '.vhd': 'vhdl_source',
            '.tb.v': 'testbench',
            '.md': 'documentation',
            '.json': 'metadata',
            '.log': 'log_file',
            '.out': 'simulation_output',
            '.vcd': 'waveform_data'
        }
        return type_map.get(suffix, 'unknown')
    
    def _get_file_size(self, file_path: str) -> int:
        """获取文件大小"""
        try:
            return Path(file_path).stat().st_size
        except:
            return 0
    
    def _get_file_description(self, file_path: str) -> str:
        """获取文件描述"""
        path = Path(file_path)
        if path.name.endswith('_tb.v'):
            return "Testbench file for simulation"
        elif path.name.endswith('.v'):
            return "Verilog design source file"
        elif path.name.endswith('_report.md'):
            return "Detailed analysis report"
        elif path.name.endswith('.json'):
            return "Metadata and metrics"
        else:
            return f"Generated artifact: {path.name}"


@dataclass
class AgentMessage:
    """智能体间标准消息格式"""
    message_id: str
    message_type: MessageType
    sender_id: str
    receiver_id: str
    timestamp: float
    conversation_id: str
    
    # 消息内容
    content: Dict[str, Any]
    
    # 可选字段
    parent_message_id: Optional[str] = None
    priority: int = 5  # 1-10
    requires_response: bool = True
    response_timeout: Optional[float] = None
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """从JSON格式解析"""
        data = json.loads(json_str)
        # 转换枚举类型
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)


@dataclass
class CoordinationDecision:
    """协调决策"""
    decision_id: str
    conversation_id: str
    current_task_id: str
    decision_type: str  # "assign_task", "continue_conversation", "complete_task", "escalate"
    
    # 决策内容
    selected_agent_id: Optional[str] = None
    next_task: Optional[TaskRequirement] = None
    reasoning: str = ""
    confidence: float = 0.0  # 0.0-1.0
    
    # 执行参数
    parameters: Optional[Dict[str, Any]] = None
    expected_duration: Optional[float] = None


class AgentCommunicationProtocol:
    """智能体通信协议管理器"""
    
    def __init__(self):
        self.message_history: List[AgentMessage] = []
        self.active_conversations: Dict[str, List[str]] = {}  # conversation_id -> message_ids
        
    def create_task_assignment_message(
        self, 
        coordinator_id: str,
        target_agent_id: str,
        task: TaskRequirement,
        conversation_id: str
    ) -> AgentMessage:
        """创建任务分配消息"""
        message_id = f"msg_{int(time.time() * 1000000)}"
        
        return AgentMessage(
            message_id=message_id,
            message_type=MessageType.TASK_ASSIGNMENT,
            sender_id=coordinator_id,
            receiver_id=target_agent_id,
            timestamp=time.time(),
            conversation_id=conversation_id,
            content={
                "task": asdict(task),
                "instructions": f"请处理任务: {task.description}",
                "format_requirements": {
                    "response_format": "json",
                    "required_fields": ["task_id", "status", "result_data", "generated_files", "quality_metrics"],
                    "file_naming_convention": "artifacts/{task_id}_{timestamp}_{filename}"
                }
            },
            requires_response=True,
            response_timeout=300.0  # 5分钟超时
        )
    
    def create_task_result_message(
        self,
        agent_id: str,
        coordinator_id: str,
        task_result: TaskResult,
        conversation_id: str,
        parent_message_id: str
    ) -> AgentMessage:
        """创建任务结果消息"""
        message_id = f"msg_{int(time.time() * 1000000)}"
        
        return AgentMessage(
            message_id=message_id,
            message_type=MessageType.TASK_RESULT,
            sender_id=agent_id,
            receiver_id=coordinator_id,
            timestamp=time.time(),
            conversation_id=conversation_id,
            parent_message_id=parent_message_id,
            content={
                "task_result": asdict(task_result),
                "summary": f"任务 {task_result.task_id} 执行状态: {task_result.status.value}",
                "recommendations": task_result.next_steps or []
            },
            requires_response=False
        )
    
    def create_coordination_request_message(
        self,
        agent_id: str,
        coordinator_id: str,
        request_type: str,
        content: Dict[str, Any],
        conversation_id: str
    ) -> AgentMessage:
        """创建协调请求消息"""
        message_id = f"msg_{int(time.time() * 1000000)}"
        
        return AgentMessage(
            message_id=message_id,
            message_type=MessageType.COORDINATION_REQUEST,
            sender_id=agent_id,
            receiver_id=coordinator_id,
            timestamp=time.time(),
            conversation_id=conversation_id,
            content={
                "request_type": request_type,
                "details": content
            },
            requires_response=True
        )
    
    def log_message(self, message: AgentMessage):
        """记录消息到历史"""
        self.message_history.append(message)
        
        # 更新对话记录
        conv_id = message.conversation_id
        if conv_id not in self.active_conversations:
            self.active_conversations[conv_id] = []
        self.active_conversations[conv_id].append(message.message_id)
    
    def get_conversation_history(self, conversation_id: str) -> List[AgentMessage]:
        """获取对话历史"""
        if conversation_id not in self.active_conversations:
            return []
        
        message_ids = self.active_conversations[conversation_id]
        return [msg for msg in self.message_history if msg.message_id in message_ids]
    
    def validate_message_format(self, message: AgentMessage) -> Dict[str, Any]:
        """验证消息格式"""
        errors = []
        warnings = []
        
        # 必填字段检查
        required_fields = ['message_id', 'message_type', 'sender_id', 'receiver_id', 'timestamp', 'conversation_id', 'content']
        for field in required_fields:
            if not hasattr(message, field) or getattr(message, field) is None:
                errors.append(f"Missing required field: {field}")
        
        # 消息类型特定验证
        if message.message_type == MessageType.TASK_RESULT:
            required_content_fields = ['task_result']
            for field in required_content_fields:
                if field not in message.content:
                    errors.append(f"Missing required content field for TASK_RESULT: {field}")
        
        # 时间戳合理性检查
        current_time = time.time()
        if message.timestamp > current_time + 60:  # 未来1分钟内算合理
            warnings.append("Message timestamp is in the future")
        elif message.timestamp < current_time - 86400:  # 超过1天算警告
            warnings.append("Message timestamp is more than 1 day old")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# 预定义的消息模板
class MessageTemplates:
    """标准消息模板"""
    
    @staticmethod
    def verilog_design_task(task_id: str, description: str, requirements: Dict[str, Any]) -> TaskRequirement:
        """Verilog设计任务模板"""
        return TaskRequirement(
            task_id=task_id,
            task_type="verilog_design",
            priority=7,
            description=description,
            requirements=requirements,
            dependencies=[],
            expected_outputs=["*.v", "*.md", "*.json"],
            constraints={
                "max_execution_time": 300,  # 5分钟
                "quality_threshold": 0.8
            }
        )
    
    @staticmethod
    def code_review_task(task_id: str, target_files: List[str], review_criteria: List[str]) -> TaskRequirement:
        """代码审查任务模板"""
        return TaskRequirement(
            task_id=task_id,
            task_type="code_review",
            priority=6,
            description=f"代码审查任务，审查文件: {', '.join(target_files)}",
            requirements={
                "target_files": target_files,
                "review_criteria": review_criteria,
                "generate_testbench": True,
                "run_simulation": True
            },
            dependencies=[],
            expected_outputs=["*_tb.v", "*_report.md", "*.json"],
            constraints={
                "max_execution_time": 600,  # 10分钟
                "quality_threshold": 0.9
            }
        )
    
    @staticmethod
    def integration_task(task_id: str, design_files: List[str], integration_requirements: Dict[str, Any]) -> TaskRequirement:
        """集成任务模板"""
        return TaskRequirement(
            task_id=task_id,
            task_type="integration",
            priority=8,
            description=f"集成任务，集成文件: {', '.join(design_files)}",
            requirements={
                "design_files": design_files,
                "integration_requirements": integration_requirements
            },
            dependencies=[],
            expected_outputs=["*_integrated.v", "*_integration_report.md"],
            constraints={
                "max_execution_time": 900,  # 15分钟
                "quality_threshold": 0.85
            }
        )


# 全局通信协议实例
agent_communication = AgentCommunicationProtocol()