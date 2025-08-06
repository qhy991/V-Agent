"""
增强实验记录器 - 清晰区分对话内容、工具调用和不同agent的信息
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging


class MessageType(Enum):
    """消息类型枚举"""
    USER_PROMPT = "user_prompt"
    ASSISTANT_RESPONSE = "assistant_response"
    SYSTEM_PROMPT = "system_prompt"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    AGENT_SWITCH = "agent_switch"
    ERROR = "error"
    INFO = "info"


class AgentType(Enum):
    """智能体类型枚举"""
    COORDINATOR = "coordinator"
    VERILOG_AGENT = "verilog_agent"
    CODE_REVIEW_AGENT = "code_review_agent"
    USER = "user"
    SYSTEM = "system"


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: float
    agent_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class ConversationMessage:
    """对话消息记录"""
    message_id: str
    timestamp: float
    agent_id: str
    agent_type: AgentType
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    parent_message_id: Optional[str] = None
    conversation_round: int = 0


@dataclass
class AgentSession:
    """智能体会话记录"""
    agent_id: str
    agent_type: AgentType
    start_time: float
    end_time: Optional[float] = None
    messages: List[ConversationMessage] = field(default_factory=list)
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    total_execution_time: float = 0.0


@dataclass
class ExperimentSession:
    """实验会话记录"""
    experiment_id: str
    start_time: float
    end_time: Optional[float] = None
    original_request: str
    success: bool = False
    error_message: Optional[str] = None
    
    # 会话管理
    current_agent_id: Optional[str] = None
    agent_sessions: Dict[str, AgentSession] = field(default_factory=dict)
    conversation_messages: List[ConversationMessage] = field(default_factory=list)
    
    # 统计信息
    total_messages: int = 0
    total_tool_calls: int = 0
    total_agents_involved: int = 0
    
    # 文件操作记录
    generated_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    
    # 性能指标
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class EnhancedExperimentRecorder:
    """增强实验记录器"""
    
    def __init__(self, experiment_id: str, output_dir: Path):
        self.experiment_id = experiment_id
        self.output_dir = output_dir
        self.session = ExperimentSession(
            experiment_id=experiment_id,
            start_time=time.time(),
            original_request=""
        )
        self.logger = logging.getLogger(f"ExperimentRecorder.{experiment_id}")
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
    
    def set_original_request(self, request: str):
        """设置原始请求"""
        self.session.original_request = request
    
    def start_agent_session(self, agent_id: str, agent_type: AgentType) -> str:
        """开始智能体会话"""
        if agent_id not in self.session.agent_sessions:
            self.session.agent_sessions[agent_id] = AgentSession(
                agent_id=agent_id,
                agent_type=agent_type,
                start_time=time.time()
            )
            self.session.total_agents_involved += 1
        
        self.session.current_agent_id = agent_id
        
        # 记录智能体切换
        self._add_message(
            agent_id=agent_id,
            agent_type=agent_type,
            message_type=MessageType.AGENT_SWITCH,
            content=f"切换到智能体: {agent_id}",
            metadata={"previous_agent": self.session.current_agent_id}
        )
        
        return agent_id
    
    def end_agent_session(self, agent_id: str, success: bool = True):
        """结束智能体会话"""
        if agent_id in self.session.agent_sessions:
            session = self.session.agent_sessions[agent_id]
            session.end_time = time.time()
            session.total_execution_time = session.end_time - session.start_time
            
            if success:
                session.success_count += 1
            else:
                session.failure_count += 1
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加用户消息"""
        return self._add_message(
            agent_id="user",
            agent_type=AgentType.USER,
            message_type=MessageType.USER_PROMPT,
            content=content,
            metadata=metadata or {}
        )
    
    def add_assistant_message(self, agent_id: str, content: str, 
                            metadata: Dict[str, Any] = None) -> str:
        """添加助手消息"""
        agent_type = self._get_agent_type(agent_id)
        return self._add_message(
            agent_id=agent_id,
            agent_type=agent_type,
            message_type=MessageType.ASSISTANT_RESPONSE,
            content=content,
            metadata=metadata or {}
        )
    
    def add_system_message(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加系统消息"""
        return self._add_message(
            agent_id="system",
            agent_type=AgentType.SYSTEM,
            message_type=MessageType.SYSTEM_PROMPT,
            content=content,
            metadata=metadata or {}
        )
    
    def add_tool_call(self, agent_id: str, tool_name: str, parameters: Dict[str, Any],
                     success: bool = True, result: Dict[str, Any] = None,
                     error_message: str = None, execution_time: float = 0.0) -> str:
        """添加工具调用记录"""
        # 创建工具调用记录
        tool_call = ToolCallRecord(
            tool_name=tool_name,
            parameters=parameters,
            timestamp=time.time(),
            agent_id=agent_id,
            success=success,
            result=result,
            error_message=error_message,
            execution_time=execution_time
        )
        
        # 添加到当前智能体会话
        if agent_id in self.session.agent_sessions:
            self.session.agent_sessions[agent_id].tool_calls.append(tool_call)
        
        # 添加到总统计
        self.session.total_tool_calls += 1
        
        # 创建工具调用消息
        message_id = self._add_message(
            agent_id=agent_id,
            agent_type=self._get_agent_type(agent_id),
            message_type=MessageType.TOOL_CALL,
            content=f"调用工具: {tool_name}",
            metadata={
                "tool_name": tool_name,
                "parameters": parameters,
                "success": success,
                "execution_time": execution_time
            }
        )
        
        # 如果有结果，添加工具结果消息
        if result:
            self._add_message(
                agent_id=agent_id,
                agent_type=self._get_agent_type(agent_id),
                message_type=MessageType.TOOL_RESULT,
                content=f"工具 {tool_name} 执行结果",
                metadata={"result": result, "success": success},
                parent_message_id=message_id
            )
        
        return message_id
    
    def add_error_message(self, agent_id: str, error_message: str, 
                         metadata: Dict[str, Any] = None) -> str:
        """添加错误消息"""
        return self._add_message(
            agent_id=agent_id,
            agent_type=self._get_agent_type(agent_id),
            message_type=MessageType.ERROR,
            content=error_message,
            metadata=metadata or {}
        )
    
    def add_info_message(self, agent_id: str, info_message: str,
                        metadata: Dict[str, Any] = None) -> str:
        """添加信息消息"""
        return self._add_message(
            agent_id=agent_id,
            agent_type=self._get_agent_type(agent_id),
            message_type=MessageType.INFO,
            content=info_message,
            metadata=metadata or {}
        )
    
    def record_file_operation(self, operation_type: str, file_path: str, 
                            agent_id: str, success: bool = True):
        """记录文件操作"""
        if operation_type == "generate" and success:
            self.session.generated_files.append(file_path)
        elif operation_type == "modify" and success:
            self.session.modified_files.append(file_path)
        
        self.add_info_message(
            agent_id=agent_id,
            info_message=f"文件操作: {operation_type} - {file_path}",
            metadata={
                "operation_type": operation_type,
                "file_path": file_path,
                "success": success
            }
        )
    
    def update_performance_metrics(self, metrics: Dict[str, Any]):
        """更新性能指标"""
        self.session.performance_metrics.update(metrics)
    
    def _add_message(self, agent_id: str, agent_type: AgentType, 
                    message_type: MessageType, content: str,
                    metadata: Dict[str, Any] = None,
                    parent_message_id: str = None) -> str:
        """添加消息到会话"""
        message_id = f"msg_{len(self.session.conversation_messages)}_{int(time.time())}"
        
        message = ConversationMessage(
            message_id=message_id,
            timestamp=time.time(),
            agent_id=agent_id,
            agent_type=agent_type,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            parent_message_id=parent_message_id,
            conversation_round=len(self.session.conversation_messages) // 2  # 每轮对话包含用户和助手消息
        )
        
        # 添加到会话消息列表
        self.session.conversation_messages.append(message)
        self.session.total_messages += 1
        
        # 添加到当前智能体会话
        if agent_id in self.session.agent_sessions:
            self.session.agent_sessions[agent_id].messages.append(message)
        
        return message_id
    
    def _get_agent_type(self, agent_id: str) -> AgentType:
        """根据智能体ID获取类型"""
        if "coordinator" in agent_id.lower():
            return AgentType.COORDINATOR
        elif "verilog" in agent_id.lower():
            return AgentType.VERILOG_AGENT
        elif "review" in agent_id.lower():
            return AgentType.CODE_REVIEW_AGENT
        elif agent_id == "user":
            return AgentType.USER
        elif agent_id == "system":
            return AgentType.SYSTEM
        else:
            return AgentType.COORDINATOR  # 默认类型
    
    def complete_experiment(self, success: bool = True, error_message: str = None):
        """完成实验"""
        self.session.end_time = time.time()
        self.session.success = success
        self.session.error_message = error_message
        
        # 结束所有活跃的智能体会话
        for agent_id in self.session.agent_sessions:
            if self.session.agent_sessions[agent_id].end_time is None:
                self.end_agent_session(agent_id, success)
    
    def save_experiment_report(self) -> Dict[str, Any]:
        """保存实验报告"""
        # 构建报告数据
        report = {
            "experiment_id": self.session.experiment_id,
            "success": self.session.success,
            "start_time": self.session.start_time,
            "end_time": self.session.end_time,
            "duration": self.session.end_time - self.session.start_time if self.session.end_time else 0,
            "original_request": self.session.original_request,
            "error_message": self.session.error_message,
            
            # 统计信息
            "total_messages": self.session.total_messages,
            "total_tool_calls": self.session.total_tool_calls,
            "total_agents_involved": self.session.total_agents_involved,
            
            # 文件操作
            "generated_files": self.session.generated_files,
            "modified_files": self.session.modified_files,
            
            # 性能指标
            "performance_metrics": self.session.performance_metrics,
            
            # 详细记录 - 按类型分类
            "conversation_history": self._format_conversation_history(),
            "agent_sessions": self._format_agent_sessions(),
            "tool_executions": self._format_tool_executions(),
            
            # 分析摘要
            "analysis_summary": self._generate_analysis_summary()
        }
        
        # 保存JSON报告
        report_path = self.output_dir / "reports" / "experiment_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存人类可读的摘要
        summary_path = self.output_dir / "reports" / "experiment_summary.txt"
        self._save_text_summary(report, summary_path)
        
        # 保存分类报告
        self._save_classified_reports(report)
        
        self.logger.info(f"📊 实验报告已保存到: {self.output_dir}")
        return report
    
    def _format_conversation_history(self) -> List[Dict[str, Any]]:
        """格式化对话历史"""
        formatted_history = []
        
        for msg in self.session.conversation_messages:
            formatted_msg = {
                "message_id": msg.message_id,
                "timestamp": msg.timestamp,
                "agent_id": msg.agent_id,
                "agent_type": msg.agent_type.value,
                "message_type": msg.message_type.value,
                "content": msg.content,
                "metadata": msg.metadata,
                "conversation_round": msg.conversation_round,
                "parent_message_id": msg.parent_message_id
            }
            formatted_history.append(formatted_msg)
        
        return formatted_history
    
    def _format_agent_sessions(self) -> Dict[str, Dict[str, Any]]:
        """格式化智能体会话"""
        formatted_sessions = {}
        
        for agent_id, session in self.session.agent_sessions.items():
            formatted_session = {
                "agent_id": session.agent_id,
                "agent_type": session.agent_type.value,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "total_execution_time": session.total_execution_time,
                "success_count": session.success_count,
                "failure_count": session.failure_count,
                "message_count": len(session.messages),
                "tool_call_count": len(session.tool_calls),
                "messages": [asdict(msg) for msg in session.messages],
                "tool_calls": [asdict(tool_call) for tool_call in session.tool_calls]
            }
            formatted_sessions[agent_id] = formatted_session
        
        return formatted_sessions
    
    def _format_tool_executions(self) -> List[Dict[str, Any]]:
        """格式化工具执行记录"""
        tool_executions = []
        
        for session in self.session.agent_sessions.values():
            for tool_call in session.tool_calls:
                tool_execution = {
                    "tool_name": tool_call.tool_name,
                    "agent_id": tool_call.agent_id,
                    "timestamp": tool_call.timestamp,
                    "parameters": tool_call.parameters,
                    "success": tool_call.success,
                    "result": tool_call.result,
                    "error_message": tool_call.error_message,
                    "execution_time": tool_call.execution_time
                }
                tool_executions.append(tool_execution)
        
        return tool_executions
    
    def _generate_analysis_summary(self) -> Dict[str, Any]:
        """生成分析摘要"""
        # 按消息类型统计
        message_type_stats = {}
        for msg in self.session.conversation_messages:
            msg_type = msg.message_type.value
            message_type_stats[msg_type] = message_type_stats.get(msg_type, 0) + 1
        
        # 按智能体统计
        agent_stats = {}
        for agent_id, session in self.session.agent_sessions.items():
            agent_stats[agent_id] = {
                "message_count": len(session.messages),
                "tool_call_count": len(session.tool_calls),
                "success_count": session.success_count,
                "failure_count": session.failure_count,
                "total_execution_time": session.total_execution_time
            }
        
        # 工具使用统计
        tool_stats = {}
        for session in self.session.agent_sessions.values():
            for tool_call in session.tool_calls:
                tool_name = tool_call.tool_name
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {"total_calls": 0, "successful_calls": 0}
                tool_stats[tool_name]["total_calls"] += 1
                if tool_call.success:
                    tool_stats[tool_name]["successful_calls"] += 1
        
        return {
            "message_type_statistics": message_type_stats,
            "agent_statistics": agent_stats,
            "tool_usage_statistics": tool_stats,
            "conversation_rounds": max([msg.conversation_round for msg in self.session.conversation_messages], default=0) + 1
        }
    
    def _save_text_summary(self, report: Dict[str, Any], summary_path: Path):
        """保存文本摘要"""
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("增强实验记录报告\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"实验ID: {report['experiment_id']}\n")
            f.write(f"实验状态: {'✅ 成功' if report['success'] else '❌ 失败'}\n")
            f.write(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report['start_time']))}\n")
            f.write(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report['end_time']))}\n")
            f.write(f"总耗时: {report['duration']:.2f} 秒\n\n")
            
            f.write("原始请求:\n")
            f.write(f"{report['original_request']}\n\n")
            
            if report['error_message']:
                f.write(f"错误信息: {report['error_message']}\n\n")
            
            f.write("统计摘要:\n")
            f.write(f"- 总消息数: {report['total_messages']}\n")
            f.write(f"- 总工具调用数: {report['total_tool_calls']}\n")
            f.write(f"- 参与智能体数: {report['total_agents_involved']}\n")
            f.write(f"- 生成文件数: {len(report['generated_files'])}\n")
            f.write(f"- 修改文件数: {len(report['modified_files'])}\n\n")
            
            # 智能体统计
            f.write("智能体统计:\n")
            for agent_id, stats in report['analysis_summary']['agent_statistics'].items():
                f.write(f"- {agent_id}:\n")
                f.write(f"  消息数: {stats['message_count']}\n")
                f.write(f"  工具调用数: {stats['tool_call_count']}\n")
                f.write(f"  成功次数: {stats['success_count']}\n")
                f.write(f"  失败次数: {stats['failure_count']}\n")
                f.write(f"  执行时间: {stats['total_execution_time']:.2f}秒\n")
            f.write("\n")
            
            # 工具使用统计
            f.write("工具使用统计:\n")
            for tool_name, stats in report['analysis_summary']['tool_usage_statistics'].items():
                success_rate = (stats['successful_calls'] / stats['total_calls']) * 100
                f.write(f"- {tool_name}: {stats['total_calls']}次调用, 成功率: {success_rate:.1f}%\n")
    
    def _save_classified_reports(self, report: Dict[str, Any]):
        """保存分类报告"""
        # 保存对话历史
        conversation_path = self.output_dir / "reports" / "conversation_history.json"
        with open(conversation_path, 'w', encoding='utf-8') as f:
            json.dump(report['conversation_history'], f, ensure_ascii=False, indent=2, default=str)
        
        # 保存工具执行记录
        tools_path = self.output_dir / "reports" / "tool_executions.json"
        with open(tools_path, 'w', encoding='utf-8') as f:
            json.dump(report['tool_executions'], f, ensure_ascii=False, indent=2, default=str)
        
        # 保存智能体会话
        agents_path = self.output_dir / "reports" / "agent_sessions.json"
        with open(agents_path, 'w', encoding='utf-8') as f:
            json.dump(report['agent_sessions'], f, ensure_ascii=False, indent=2, default=str)
        
        # 保存分析摘要
        analysis_path = self.output_dir / "reports" / "analysis_summary.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(report['analysis_summary'], f, ensure_ascii=False, indent=2, default=str)
    
    def get_conversation_by_type(self, message_type: MessageType) -> List[ConversationMessage]:
        """按消息类型获取对话"""
        return [msg for msg in self.session.conversation_messages if msg.message_type == message_type]
    
    def get_agent_conversation(self, agent_id: str) -> List[ConversationMessage]:
        """获取特定智能体的对话"""
        return [msg for msg in self.session.conversation_messages if msg.agent_id == agent_id]
    
    def get_tool_calls_by_agent(self, agent_id: str) -> List[ToolCallRecord]:
        """获取特定智能体的工具调用"""
        if agent_id in self.session.agent_sessions:
            return self.session.agent_sessions[agent_id].tool_calls
        return []
    
    def get_tool_calls_by_name(self, tool_name: str) -> List[ToolCallRecord]:
        """按工具名称获取工具调用"""
        tool_calls = []
        for session in self.session.agent_sessions.values():
            for tool_call in session.tool_calls:
                if tool_call.tool_name == tool_name:
                    tool_calls.append(tool_call)
        return tool_calls 