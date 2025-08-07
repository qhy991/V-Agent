#!/usr/bin/env python3
"""
基于LLM的协调智能体 - 强化版本

Enhanced LLM-Driven Coordinator Agent
"""

import asyncio
import json
import time
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.base_agent import TaskMessage
from core.enums import AgentCapability, AgentStatus
from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from core.enhanced_logging_config import get_agent_logger
from core.llm_communication import UnifiedLLMClientManager, SystemPromptBuilder, CallType


class TaskType(Enum):
    """任务类型枚举"""
    DESIGN = "design"
    VERIFICATION = "verification"
    ANALYSIS = "analysis"
    DEBUG = "debug"
    COMPOSITE = "composite"
    UNKNOWN = "unknown"


class TaskPriority(Enum):
    """任务优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AgentInfo:
    """智能体信息 - 增强版本"""
    agent_id: str
    agent_instance: EnhancedBaseAgent
    capabilities: Set[AgentCapability]
    specialty: str
    status: AgentStatus = AgentStatus.IDLE
    conversation_id: Optional[str] = None
    last_used: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0
    total_execution_time: float = 0.0
    average_response_time: float = 0.0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    preferred_task_types: Set[TaskType] = field(default_factory=set)
    blacklisted_task_types: Set[TaskType] = field(default_factory=set)


@dataclass
class TaskContext:
    """任务上下文 - 增强版本"""
    task_id: str
    original_request: str
    task_type: TaskType = TaskType.UNKNOWN
    priority: TaskPriority = TaskPriority.MEDIUM
    current_stage: str = "initial"
    assigned_agent: Optional[str] = None
    agent_results: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    iteration_count: int = 0
    max_iterations: int = 10
    external_testbench_path: Optional[str] = None
    quality_score: float = 0.0
    completion_status: str = "pending"
    error_history: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    agent_assignments: List[Dict[str, Any]] = field(default_factory=list)
    design_file_path: Optional[str] = None
    # 🆕 添加实验路径字段，为每个任务创建独立的实验目录
    experiment_path: Optional[str] = None
    
    # 🆕 增强数据收集字段 - 用于Gradio可视化
    tool_executions: List[Dict[str, Any]] = field(default_factory=list)
    agent_interactions: List[Dict[str, Any]] = field(default_factory=list) 
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    workflow_stages: List[Dict[str, Any]] = field(default_factory=list)
    file_operations: List[Dict[str, Any]] = field(default_factory=list)
    execution_timeline: List[Dict[str, Any]] = field(default_factory=list)
    # 🆕 新增：LLM对话记录
    llm_conversations: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_conversation_message(self, role: str, content: str, agent_id: str = None, 
                               tool_info: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        """添加对话消息到历史记录"""
        # 🔧 安全处理content参数，确保它是字符串
        if content is None:
            safe_content = ""
        elif hasattr(content, '__await__'):  # 检查是否为协程对象
            safe_content = f"[协程对象: {type(content).__name__}]"
        else:
            safe_content = str(content)
        
        message = {
            "timestamp": time.time(),
            "role": role,
            "content": safe_content,
            "agent_id": agent_id or "unknown",
        }
        
        if tool_info:
            message["tool_info"] = tool_info
        if metadata:
            message["metadata"] = metadata
            
        self.conversation_history.append(message)
        
        # 记录日志
        import logging
        logger = logging.getLogger("TaskContext")
        logger.info(f"📝 记录对话消息: {role} - {agent_id or 'unknown'} - 长度: {len(safe_content)}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话统计摘要"""
        agents_involved = list(set(msg.get('agent_id', 'unknown') for msg in self.conversation_history))
        message_types = {}
        
        for msg in self.conversation_history:
            role = msg.get('role', 'unknown')
            message_types[role] = message_types.get(role, 0) + 1
        
        return {
            "total_messages": len(self.conversation_history),
            "agents_involved": agents_involved,
            "message_types": message_types,
            "conversation_duration": time.time() - self.start_time if self.conversation_history else 0
        }
    
    def get_agent_conversation_count(self, agent_id: str) -> int:
        """获取特定智能体的对话消息数量"""
        return len([msg for msg in self.conversation_history if msg.get('agent_id') == agent_id])
    
    def get_tool_calls_summary(self) -> Dict[str, Any]:
        """获取工具调用统计摘要"""
        tool_calls = [msg for msg in self.conversation_history if msg.get('tool_info')]
        
        tool_names = []
        successful_calls = 0
        
        for msg in tool_calls:
            tool_info = msg.get('tool_info', {})
            if 'tool_name' in tool_info:
                tool_names.append(tool_info['tool_name'])
            if tool_info.get('success', False):
                successful_calls += 1
        
        return {
            "total_tool_calls": len(tool_calls),
            "successful_calls": successful_calls,
            "failure_rate": (len(tool_calls) - successful_calls) / max(len(tool_calls), 1),
            "unique_tools_used": list(set(tool_names)),
            "tool_usage_count": {name: tool_names.count(name) for name in set(tool_names)}
        }
    
    def add_tool_execution(self, tool_name: str, parameters: Dict[str, Any], 
                          agent_id: str, success: bool = True, 
                          result: Any = None, error: str = None, 
                          execution_time: float = 0.0):
        """记录工具调用执行"""
        tool_execution = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "parameters": parameters,
            "agent_id": agent_id,
            "success": success,
            "result": str(result)[:500] if result else None,  # 限制结果长度
            "error": error,
            "execution_time": execution_time
        }
        self.tool_executions.append(tool_execution)
        
        # 同时记录到执行时间线
        self.execution_timeline.append({
            "timestamp": time.time(),
            "event_type": "tool_execution",
            "agent_id": agent_id,
            "tool_name": tool_name,
            "success": success,
            "duration": execution_time
        })
    
    def add_file_operation(self, operation_type: str, file_path: str, 
                          agent_id: str, success: bool = True, 
                          file_size: int = 0, error: str = None):
        """记录文件操作"""
        file_operation = {
            "timestamp": time.time(),
            "operation_type": operation_type,  # read, write, create, delete
            "file_path": file_path,
            "agent_id": agent_id,
            "success": success,
            "file_size": file_size,
            "error": error
        }
        self.file_operations.append(file_operation)
        
        # 同时记录到执行时间线
        self.execution_timeline.append({
            "timestamp": time.time(),
            "event_type": "file_operation",
            "agent_id": agent_id,
            "operation_type": operation_type,
            "file_path": file_path,
            "success": success
        })
    
    def add_workflow_stage(self, stage_name: str, description: str, 
                          agent_id: str = None, duration: float = 0.0, 
                          success: bool = True, metadata: Dict[str, Any] = None):
        """记录工作流阶段"""
        stage = {
            "timestamp": time.time(),
            "stage_name": stage_name,
            "description": description,
            "agent_id": agent_id,
            "duration": duration,
            "success": success,
            "metadata": metadata or {}
        }
        self.workflow_stages.append(stage)
        
        # 同时记录到执行时间线
        self.execution_timeline.append({
            "timestamp": time.time(),
            "event_type": "workflow_stage",
            "stage_name": stage_name,
            "agent_id": agent_id,
            "success": success,
            "duration": duration
        })
    
    def update_performance_metrics(self, metrics: Dict[str, Any]):
        """更新性能指标"""
        self.performance_metrics.update(metrics)
    
    def get_data_collection_summary(self) -> Dict[str, Any]:
        """获取数据收集摘要"""
        return {
            "tool_executions": {
                "total": len(self.tool_executions),
                "successful": len([t for t in self.tool_executions if t.get("success", True)]),
                "failed": len([t for t in self.tool_executions if not t.get("success", True)]),
                "unique_tools": list(set(t.get("tool_name") for t in self.tool_executions)),
                "total_execution_time": sum(t.get("execution_time", 0) or 0 for t in self.tool_executions)
            },
            "file_operations": {
                "total": len(self.file_operations),
                "successful": len([f for f in self.file_operations if f.get("success", True)]),
                "failed": len([f for f in self.file_operations if not f.get("success", True)]),
                "operation_types": list(set(f.get("operation_type") for f in self.file_operations)),
                "total_file_size": sum(f.get("file_size", 0) or 0 for f in self.file_operations)
            },
            "workflow_stages": {
                "total": len(self.workflow_stages),
                "successful": len([w for w in self.workflow_stages if w.get("success", True)]),
                "failed": len([w for w in self.workflow_stages if not w.get("success", True)]),
                "total_duration": sum(w.get("duration", 0) or 0 for w in self.workflow_stages)
            },
            "agent_interactions": {
                "total": len(self.agent_interactions),
                "unique_agents": list(set(i.get("target_agent_id") for i in self.agent_interactions)),
                "successful": len([i for i in self.agent_interactions if i.get("success", True)]),
                "failed": len([i for i in self.agent_interactions if not i.get("success", True)])
            },
            "execution_timeline": {
                "total_events": len(self.execution_timeline),
                "event_types": list(set(e.get("event_type") for e in self.execution_timeline))
            },
            "llm_conversations": {
                "total": len(self.llm_conversations),
                "successful": len([l for l in self.llm_conversations if l.get("success", True)]),
                "failed": len([l for l in self.llm_conversations if not l.get("success", True)]),
                "unique_agents": list(set(l.get("agent_id") for l in self.llm_conversations)),
                "unique_models": list(set(l.get("model_name") for l in self.llm_conversations)),
                "total_duration": sum(l.get("duration", 0) or 0 for l in self.llm_conversations),
                "first_calls": len([l for l in self.llm_conversations if l.get("is_first_call", False)]),
                "total_tokens": sum(l.get("total_tokens", 0) or 0 for l in self.llm_conversations)
            }
        }
    
    def add_llm_conversation(self, agent_id: str, conversation_id: str,
                           system_prompt: str, user_message: str, 
                           assistant_response: str, model_name: str = None,
                           duration: float = 0.0, success: bool = True,
                           error_info: str = None, is_first_call: bool = False,
                           temperature: float = None, max_tokens: int = None,
                           prompt_tokens: int = None, completion_tokens: int = None,
                           total_tokens: int = None):
        """记录LLM对话"""
        # 安全处理可能为None的字符串参数
        safe_system_prompt = system_prompt or ""
        safe_user_message = user_message or ""
        safe_assistant_response = assistant_response or ""
        
        llm_conversation = {
            "timestamp": time.time(),
            "agent_id": agent_id,
            "conversation_id": conversation_id,
            "system_prompt": safe_system_prompt[:1000] + ("..." if len(safe_system_prompt) > 1000 else ""),  # 限制长度
            "user_message": safe_user_message[:2000] + ("..." if len(safe_user_message) > 2000 else ""),  # 限制长度
            "assistant_response": safe_assistant_response[:2000] + ("..." if len(safe_assistant_response) > 2000 else ""),  # 限制长度
            "model_name": model_name,
            "duration": duration,
            "success": success,
            "error_info": error_info,
            "is_first_call": is_first_call,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
        self.llm_conversations.append(llm_conversation)
        
        # 同时记录到执行时间线
        self.execution_timeline.append({
            "timestamp": time.time(),
            "event_type": "llm_conversation",
            "agent_id": agent_id,
            "conversation_id": conversation_id,
            "model_name": model_name,
            "success": success,
            "duration": duration,
            "is_first_call": is_first_call
        })


class LLMCoordinatorAgent(EnhancedBaseAgent):
    """
    基于LLM的协调智能体 - 强化版本
    
    特点：
    1. 智能任务类型识别和分类
    2. 基于历史表现的智能体选择
    3. 严格的任务职责分离控制
    4. 增强的结果质量分析
    5. 智能错误恢复和重试机制
    6. 详细的执行监控和日志
    """
    
    def __init__(self, config: FrameworkConfig = None):
        # 初始化配置
        self.config = config or FrameworkConfig.from_env()
        
        super().__init__(
            agent_id="llm_coordinator_agent",
            role="coordinator",
            capabilities={
                AgentCapability.TASK_COORDINATION,
                AgentCapability.WORKFLOW_MANAGEMENT,
                AgentCapability.SPECIFICATION_ANALYSIS,
                AgentCapability.CODE_REVIEW,
                AgentCapability.QUALITY_ANALYSIS,
                AgentCapability.SYSTEM_MONITORING
            },
            config=self.config
        )
        
        # 记录启动时间
        self.start_time = time.time()
        
        # 初始化LLM通信模块
        self.llm_manager = UnifiedLLMClientManager(
            agent_id="llm_coordinator_agent",
            role="coordinator",
            config=self.config
        )
        self.prompt_builder = SystemPromptBuilder()
        
        # 设置专用日志器
        self.agent_logger = get_agent_logger('LLMCoordinatorAgent')
        
        # 注册的智能体
        self.registered_agents: Dict[str, AgentInfo] = {}
        
        # 任务上下文管理
        self.active_tasks: Dict[str, TaskContext] = {}
        
        # 任务类型识别器
        self.task_patterns = self._initialize_task_patterns()
        
        # 协调工具
        self._register_enhanced_coordination_tools()
        
        # 性能监控
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_completion_time": 0.0,
            "agent_utilization": {}
        }
        
        self.logger.debug("🧠 LLM协调智能体初始化完成")
    
    def _initialize_task_patterns(self) -> Dict[TaskType, List[str]]:
        """初始化任务类型识别模式"""
        return {
            TaskType.DESIGN: [
                r"设计.*模块", r"生成.*代码", r"实现.*功能", r"创建.*电路",
                r"design.*module", r"generate.*code", r"implement.*function",
                r"verilog.*module", r"hdl.*design", r"circuit.*design",
                r"模块设计", r"代码生成", r"功能实现", r"电路设计"
            ],
            TaskType.VERIFICATION: [
                r"测试.*验证", r"仿真.*测试", r"生成.*testbench", r"验证.*功能",
                r"test.*verification", r"simulation.*test", r"generate.*testbench",
                r"verify.*function", r"testbench.*generation", r"simulation.*verification",
                r"代码审查", r"质量分析", r"错误检查", r"功能验证"
            ],
            TaskType.ANALYSIS: [
                r"分析.*代码", r"质量.*评估", r"性能.*分析", r"代码.*审查",
                r"analyze.*code", r"quality.*assessment", r"performance.*analysis",
                r"code.*review", r"static.*analysis", r"dynamic.*analysis",
                r"代码分析", r"质量评估", r"性能分析", r"静态分析"
            ],
            TaskType.DEBUG: [
                r"调试.*错误", r"修复.*问题", r"错误.*分析", r"问题.*解决",
                r"debug.*error", r"fix.*issue", r"error.*analysis", r"problem.*solving",
                r"bug.*fix", r"error.*correction", r"issue.*resolution",
                r"错误修复", r"问题调试", r"bug修复", r"错误分析"
            ]
        }
    
    def _register_enhanced_coordination_tools(self):
        """注册增强的协调工具"""
        
        # 1. 智能任务分配工具
        self.register_enhanced_tool(
            name="assign_task_to_agent",
            func=self._tool_assign_task_to_agent,
            description="智能分配任务给最合适的智能体，基于任务类型、智能体能力和历史表现",
            security_level="high",
            category="coordination",
            schema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "目标智能体ID（必须是enhanced_real_verilog_agent或enhanced_real_code_review_agent）",
                        "enum": ["enhanced_real_verilog_agent", "enhanced_real_code_review_agent"]
                    },
                    "task_description": {
                        "type": "string",
                        "description": "详细的任务描述和要求",
                        "minLength": 10,
                        "maxLength": 5000
                    },
                    "expected_output": {
                        "type": "string",
                        "description": "期望的输出格式和内容",
                        "default": "",
                        "maxLength": 2000
                    },
                    "task_type": {
                        "type": "string",
                        "enum": ["design", "verification", "analysis", "debug", "composite"],
                        "description": "任务类型分类"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "default": "medium",
                        "description": "任务优先级"
                    }
                },
                "required": ["agent_id", "task_description"]
            }
        )
        
        # 2. 增强结果分析工具
        self.register_enhanced_tool(
            name="analyze_agent_result",
            func=self._tool_analyze_agent_result,
            description="深度分析智能体执行结果，评估质量、完整性和下一步行动",
            security_level="high",
            category="coordination",
            schema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "执行任务的智能体ID"
                    },
                    "result": {
                        "type": "object",
                        "description": "智能体执行结果的详细信息"
                    },
                    "task_context": {
                        "type": "object",
                        "description": "当前任务上下文信息",
                        "default": {}
                    },
                    "quality_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "default": 80,
                        "description": "质量评估阈值"
                    }
                },
                "required": ["agent_id", "result"]
            }
        )
        
        # 3. 智能任务完成检查工具
        self.register_enhanced_tool(
            name="check_task_completion",
            func=self._tool_check_task_completion,
            description="智能检查任务完成状态，评估整体质量和缺失项",
            security_level="high",
            category="coordination",
            schema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务ID"
                    },
                    "all_results": {
                        "type": "object",
                        "description": "所有智能体的执行结果汇总"
                    },
                    "original_requirements": {
                        "type": "string",
                        "description": "原始任务需求描述"
                    },
                    "completion_criteria": {
                        "type": "object",
                        "description": "完成标准定义",
                        "default": {}
                    }
                },
                "required": ["task_id", "all_results", "original_requirements"]
            }
        )
        
        # 4. 智能体状态和性能查询工具
        self.register_enhanced_tool(
            name="query_agent_status",
            func=self._tool_query_agent_status,
            description="查询智能体详细状态、性能指标和历史表现",
            security_level="normal",
            category="coordination",
            schema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "智能体ID",
                        "enum": ["enhanced_real_verilog_agent", "enhanced_real_code_review_agent"]
                    },
                    "include_performance": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含性能指标"
                    },
                    "include_history": {
                        "type": "boolean",
                        "default": False,
                        "description": "是否包含历史记录"
                    }
                },
                "required": ["agent_id"]
            }
        )
        
        # 5. 新增：智能任务类型识别工具
        self.register_enhanced_tool(
            name="identify_task_type",
            func=self._tool_identify_task_type,
            description="智能识别任务类型，为任务分配提供决策支持",
            security_level="normal",
            category="analysis",
            schema={
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": "用户请求内容",
                        "minLength": 5,
                        "maxLength": 10000
                    },
                    "context": {
                        "type": "object",
                        "description": "任务上下文信息",
                        "default": {}
                    }
                },
                "required": ["user_request"]
            }
        )
        
        # 6. 新增：智能体选择推荐工具
        self.register_enhanced_tool(
            name="recommend_agent",
            func=self._tool_recommend_agent,
            description="基于任务特征和智能体能力推荐最合适的智能体",
            security_level="normal",
            category="coordination",
            schema={
                "type": "object",
                "properties": {
                    "task_type": {
                        "type": "string",
                        "enum": ["design", "verification", "analysis", "debug", "composite"],
                        "description": "任务类型"
                    },
                    "task_description": {
                        "type": "string",
                        "description": "任务描述",
                        "minLength": 10
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "default": "medium",
                        "description": "任务优先级"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "任务约束条件",
                        "default": {}
                    }
                },
                "required": ["task_type", "task_description"]
            }
        )
        
        # 7. 新增：最终答案工具
        self.register_enhanced_tool(
            name="provide_final_answer",
            func=self._tool_provide_final_answer,
            description="当所有任务都已完成，调用此工具来生成并提供最终的、完整的答案给用户。",
            security_level="normal",
            category="coordination",
            schema={
                "type": "object",
                "properties": {
                    "final_summary": {
                        "type": "string",
                        "description": "对整个任务执行过程和最终结果的详细总结。"
                    },
                    "task_status": {
                        "type": "string",
                        "description": "任务的最终状态 (例如：'成功', '失败', '部分完成')."
                    },
                    "results_summary": {
                        "type": "object",
                        "description": "所有智能体产生的结果的简要汇总。"
                    }
                },
                "required": ["final_summary", "task_status"]
            }
        )
        
        # 8. 新增：工具使用指导工具
        self.register_enhanced_tool(
            name="get_tool_usage_guide",
            func=self._tool_get_tool_usage_guide,
            description="获取LLMCoordinatorAgent的工具使用指导，包括可用工具、参数说明、调用示例和最佳实践。",
            security_level="normal",
            category="help",
            schema={
                "type": "object",
                "properties": {
                    "include_examples": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含调用示例"
                    },
                    "include_best_practices": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含最佳实践"
                    }
                },
                "additionalProperties": False
            }
        )
    
    async def _build_enhanced_system_prompt(self) -> str:
        """构建支持动态决策和多智能体协作的系统提示词"""
        
        # 使用SystemPromptBuilder构建系统提示词
        return await self.prompt_builder.build_system_prompt(
            role="coordinator",
            call_type=CallType.FUNCTION_CALLING,
            agent_id=self.agent_id,
            capabilities=self._capabilities,
            metadata={
                "has_tools": hasattr(self, 'enhanced_tools') and bool(self.enhanced_tools),
                "tools_count": len(self.enhanced_tools) if hasattr(self, 'enhanced_tools') else 0
            }
        )
    async def register_agent(self, agent: EnhancedBaseAgent):
        """注册智能体"""
        agent_info = AgentInfo(
            agent_id=agent.agent_id,
            agent_instance=agent,
            capabilities=agent.get_capabilities(),
            specialty=agent.get_specialty_description()
        )
        
        self.registered_agents[agent.agent_id] = agent_info
        self.logger.info(f"✅ 注册智能体: {agent.agent_id} ({agent_info.specialty})")
    
    async def coordinate_task(self, user_request: str, 
                            conversation_id: str = None,
                            max_iterations: int = 10,
                            external_testbench_path: str = None) -> Dict[str, Any]:
        """
        协调任务执行
        
        Args:
            user_request: 用户请求
            conversation_id: 对话ID
            max_iterations: 最大迭代次数
            external_testbench_path: 外部提供的testbench文件路径
            
        Returns:
            协调结果
        """
        self.logger.info(f"🚀 开始协调任务: {user_request[:100]}...")
        
        # 生成任务ID
        task_id = f"task_{int(time.time())}"
        
        # 🆕 创建独立的实验目录
        from core.experiment_manager import ExperimentManager
        experiment_manager = ExperimentManager()
        
        # 🎯 优化：使用智能实验名称生成
        experiment_name = experiment_manager.generate_experiment_name(user_request, task_type="design")
        
        # 创建实验
        experiment_info = experiment_manager.create_experiment(
            experiment_name=experiment_name,
            task_description=user_request,
            metadata={
                "task_id": task_id,
                "created_by": "llm_coordinator_agent",
                "conversation_id": conversation_id
            }
        )
        
        # 创建任务上下文，包含实验路径
        task_context = TaskContext(
            task_id=task_id,
            original_request=user_request,
            max_iterations=max_iterations,
            experiment_path=experiment_info.workspace_path
        )
        
        # 🆕 记录初始用户请求到对话历史
        task_context.add_conversation_message(
            role="user",
            content=user_request,
            agent_id="user",
            metadata={"task_id": task_id, "conversation_id": conversation_id}
        )
        
        # 如果提供了外部testbench，添加到任务上下文
        if external_testbench_path:
            task_context.external_testbench_path = external_testbench_path
            self.logger.info(f"📁 使用外部testbench: {external_testbench_path}")
            # 记录外部testbench信息
            task_context.add_conversation_message(
                role="system",
                content=f"使用外部testbench文件: {external_testbench_path}",
                agent_id=self.agent_id,
                metadata={"type": "external_testbench"}
            )
        
        self.active_tasks[task_id] = task_context
        
        # 🆕 设置任务上下文到当前实例，用于后续对话记录
        self.current_task_context = task_context
        
        try:
            # 构建协调任务
            coordination_task = self._build_coordination_task(user_request, task_context)
            
            # 🆕 记录系统提示（协调任务）到对话历史
            task_context.add_conversation_message(
                role="system",
                content=coordination_task,
                agent_id=self.agent_id,
                metadata={"type": "coordination_task", "task_stage": "initial"}
            )
            
            # 使用Function Calling执行协调
            result = await self.process_with_function_calling(
                user_request=coordination_task,
                max_iterations=max_iterations,
                conversation_id=conversation_id,
                preserve_context=True,
                enable_self_continuation=True,
                max_self_iterations=3
            )
            
            # 🔧 新增：格式修复 - 如果LLM输出了错误格式，尝试自动修复
            result = self._fix_tool_call_format(result)
            
            # 🆕 记录协调器的响应到对话历史
            task_context.add_conversation_message(
                role="assistant",
                content=result,
                agent_id=self.agent_id,
                metadata={"type": "coordination_response", "task_stage": "initial"}
            )
            
            # 🔍 检查是否实际调用了工具
            self.logger.info(f"🔍 检查工具调用: 结果长度={len(result)}, 内容预览={result[:100]}...")
            tools_executed = self._has_executed_tools(result)
            self.logger.info(f"🔍 工具调用检查结果: {tools_executed}")
            
            if not tools_executed:
                self.logger.warning("⚠️ 协调智能体没有调用任何工具，强制重新执行")
                self.logger.info(f"🔍 原始结果内容: {result[:200]}...")
                
                # 强制重新执行，使用更明确的指令
                forced_task = self._build_forced_coordination_task(user_request, task_context)
                self.logger.info(f"🚨 强制重新执行，任务长度: {len(forced_task)} 字符")
                
                # 使用更严格的参数进行强制重新执行
                result = await self.process_with_function_calling(
                    user_request=forced_task,
                    max_iterations=1,  # 限制为1次迭代，强制立即执行
                    conversation_id=f"{conversation_id}_forced",
                    preserve_context=False,  # 不保留上下文，重新开始
                    enable_self_continuation=False,  # 禁用自主继续
                    max_self_iterations=0  # 禁用自我继续
                )
                
                # 再次检查是否执行了工具
                if not self._has_executed_tools(result):
                    self.logger.error("❌ 强制重新执行后仍未调用工具，返回错误信息")
                    self.logger.error(f"🔍 强制执行结果: {result[:200]}...")
                    return {
                        "success": False,
                        "error": "协调智能体无法执行工具调用，请检查系统配置",
                        "task_id": task_id,
                        "debug_info": {
                            "original_result": result[:500],
                            "forced_result": result[:500],
                            "tool_detection_failed": True
                        }
                    }
            
            # 🔍 新增：检查是否调用了assign_task_to_agent工具
            self.logger.info(f"🔍 检查是否调用了assign_task_to_agent工具...")
            assign_task_called = self._check_assign_task_called(result)
            self.logger.info(f"🔍 assign_task_to_agent调用检查: {assign_task_called}")
            
            if not assign_task_called:
                self.logger.warning("⚠️ 没有调用assign_task_to_agent工具，强制调用")
                # 强制调用assign_task_to_agent
                forced_assign_result = await self._force_assign_task(user_request, task_context)
                if not forced_assign_result.get("success", False):
                    self.logger.error("❌ 强制分配任务失败")
                    return {
                        "success": False,
                        "error": "强制分配任务失败",
                        "task_id": task_id,
                        "debug_info": forced_assign_result
                    }
            
            # 🔄 开始持续协调循环 - 监听智能体结果并继续协调
            final_result = await self._run_coordination_loop(task_context, result, conversation_id, max_iterations)
            
            # 🆕 记录任务完成
            task_context.add_conversation_message(
                role="system",
                content=f"任务协调完成，任务ID: {task_id}",
                agent_id=self.agent_id,
                metadata={"type": "task_completion", "success": True}
            )
            
            self.logger.info(f"✅ 任务协调完成: {task_id}, 对话历史长度: {len(task_context.conversation_history)}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"❌ 任务协调失败: {str(e)}")
            
            # 🆕 记录错误到对话历史
            if 'task_context' in locals():
                task_context.add_conversation_message(
                    role="error",
                    content=f"任务协调失败: {str(e)}",
                    agent_id=self.agent_id,
                    metadata={"type": "task_error", "error_type": type(e).__name__}
                )
            
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
        finally:
            # 清理任务上下文
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    def _fix_tool_call_format(self, result: str) -> str:
        """修复工具调用格式 - 将错误的单工具格式转换为正确的tool_calls数组格式"""
        if not isinstance(result, str) or not result.strip():
            return result
        
        # 提取JSON内容
        json_content = self._extract_json_from_response(result.strip())
        if not json_content:
            return result
        
        try:
            data = json.loads(json_content)
            
            # 检查是否是错误的单个工具格式
            if "tool_name" in data and "parameters" in data and "tool_calls" not in data:
                self.logger.warning(f"🔧 检测到错误的单工具格式，自动修复为tool_calls数组格式")
                
                # 转换为正确的格式
                fixed_data = {
                    "tool_calls": [
                        {
                            "tool_name": data["tool_name"],
                            "parameters": data["parameters"]
                        }
                    ]
                }
                
                # 生成修复后的响应
                fixed_json = json.dumps(fixed_data, ensure_ascii=False, indent=2)
                fixed_result = f"```json\n{fixed_json}\n```"
                
                self.logger.info(f"✅ 已修复工具调用格式：{data['tool_name']}")
                return fixed_result
            
        except json.JSONDecodeError:
            self.logger.debug("JSON解析失败，保持原始格式")
        
        return result

    def _has_executed_tools(self, result: str) -> bool:
        """检查并修复LLM的回复，确保是有效的工具调用JSON。"""
        if not isinstance(result, str) or not result.strip():
            self.logger.debug(f"🔍 工具检测失败: 结果为空或非字符串类型")
            return False
        
        # 提取JSON内容，支持markdown代码块格式
        json_content = self._extract_json_from_response(result.strip())
        if not json_content:
            self.logger.debug(f"🔍 工具检测失败: 无法提取JSON内容")
            return False
            
        try:
            data = json.loads(json_content)
            self.logger.debug(f"🔍 解析JSON成功: {list(data.keys())}")
            
            # 🔧 修复：检查是否是错误的单个工具格式，并自动转换为正确的tool_calls格式
            if "tool_name" in data and "parameters" in data and "tool_calls" not in data:
                self.logger.warning(f"🔧 检测到错误的单工具格式，自动转换为tool_calls数组格式")
                # 转换为正确的格式
                fixed_data = {
                    "tool_calls": [
                        {
                            "tool_name": data["tool_name"],
                            "parameters": data["parameters"]
                        }
                    ]
                }
                # 更新result（用于后续处理）
                fixed_json = json.dumps(fixed_data, ensure_ascii=False, indent=2)
                # 这里我们不能直接修改传入的result，但可以记录问题
                self.logger.info(f"🔧 修复后的格式: {fixed_json}")
                return True  # 格式可以修复，认为是有效的工具调用
            
            # 检查正确的tool_calls格式
            if "tool_calls" in data and isinstance(data["tool_calls"], list) and len(data["tool_calls"]) > 0:
                # 进一步检查tool_calls列表中的元素是否合法
                call = data["tool_calls"][0]
                if "tool_name" in call and "parameters" in call:
                    tool_name = call["tool_name"]
                    self.logger.info(f"✅ 检测到有效工具调用: {tool_name}")
                    return True
                else:
                    self.logger.debug(f"🔍 工具调用格式不完整: {call}")
            else:
                self.logger.debug(f"🔍 未找到有效的tool_calls: {data}")
            return False
        except json.JSONDecodeError as e:
            self.logger.debug(f"🔍 JSON解析失败: {e}")
            return False
    
    def _extract_json_from_response(self, response: str) -> str:
        """从响应中提取JSON内容，支持markdown代码块格式"""
        if not response:
            return ""
        
        # 如果直接以{开头，直接返回
        if response.startswith('{'):
            return response
        
        # 处理markdown代码块格式
        import re
        
        # 匹配 ```json ... ``` 格式
        json_block_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_block_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 匹配 ``` ... ``` 格式（可能没有语言标识）
        code_block_pattern = r'```\s*(.*?)\s*```'
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # 检查是否是JSON格式
            if content.startswith('{') and content.endswith('}'):
                return content
        
        # 尝试查找JSON对象
        json_pattern = r'\{.*?\}'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            return match.group(0)
        
        return ""
    
    def _build_forced_coordination_task(self, user_request: str, task_context: TaskContext) -> str:
        """构建一个极度强制的协调任务，只要求调用第一个工具。"""
        
        # 获取第一个必须调用的工具信息
        first_tool_schema = self.get_tool_schema("identify_task_type")
        
        # Escape quotes in user_request
        escaped_user_request = user_request.replace('"', '\\"')
        
        # 获取LLMCoordinatorAgent的工具使用指导（简化版）
        coordinator_guide_simple = """
**🛠️ 正确的工具调用方式**:
1. identify_task_type - 识别任务类型
2. recommend_agent - 推荐智能体
3. assign_task_to_agent - 分配任务给智能体

⚠️ **严禁直接调用智能体名称作为工具**:
❌ enhanced_real_verilog_agent
❌ enhanced_real_code_review_agent
✅ 使用 assign_task_to_agent 工具来分配任务
"""

        return f"""
# 🚨🚨🚨 强制指令 🚨🚨🚨
你必须立即调用 `assign_task_to_agent` 工具来分配任务。

**用户需求**:
{user_request}

{coordinator_guide_simple}

# ✅ 唯一正确的工具调用格式:
```json
{{
    "tool_calls": [
        {{
            "tool_name": "assign_task_to_agent",
            "parameters": {{
                "agent_id": "enhanced_real_verilog_agent",
                "task_description": "根据用户需求设计Verilog模块，专注于模块设计和代码实现",
                "expected_output": "生成完整的Verilog代码文件",
                "task_type": "design",
                "priority": "medium"
            }}
        }}
    ]
}}
```

# 🚨🚨🚨 严格要求 🚨🚨🚨
- ✅ 只能调用 `assign_task_to_agent` 工具
- ❌ 绝对禁止调用智能体名称作为工具
- ❌ 绝对禁止使用 enhanced_real_verilog_agent 作为 tool_name
- ❌ 绝对禁止使用 enhanced_real_code_review_agent 作为 tool_name
- ❌ 不要生成任何其他内容
- ❌ 不要生成任何描述性文本
- ❌ 不要解释你的策略
- ❌ 不要分析任务
- ❌ 不要使用markdown格式
- ❌ 不要生成表格
- ✅ 只生成工具调用JSON

⚡ 立即执行: 复制上面的JSON，不要修改任何内容，立即生成。
"""
    
    def _build_coordination_task(self, user_request: str, task_context: TaskContext) -> str:
        """构建协调任务描述"""
        
        # 构建可用智能体信息
        agents_info = []
        for agent_id, agent_info in self.registered_agents.items():
            capabilities = ", ".join([cap.value for cap in agent_info.capabilities])
            agents_info.append(f"- {agent_id}: {agent_info.specialty} (能力: {capabilities})")
        
        agents_section = "\n".join(agents_info) if agents_info else "暂无可用智能体"
        
        # 构建外部testbench信息
        external_testbench_info = ""
        if hasattr(task_context, 'external_testbench_path') and task_context.external_testbench_path:
            external_testbench_info = f"""

**📁 外部Testbench**:
- 路径: {task_context.external_testbench_path}
- 说明: 用户已提供testbench文件，审查智能体应直接使用此文件进行测试，无需生成新的testbench
- 工作模式: 审查智能体专注于代码审查、测试执行和问题修复，跳过testbench生成步骤"""

        # 获取LLMCoordinatorAgent的工具使用指导
        coordinator_tool_guide = self._get_agent_specific_tool_guide("llm_coordinator_agent")

        return f"""
🧠 协调任务

**用户需求**:
{user_request}

**任务ID**: {task_context.task_id}
**当前阶段**: {task_context.current_stage}
**已执行迭代**: {task_context.iteration_count}/{task_context.max_iterations}

**可用智能体**:
{agents_section}
{external_testbench_info}

**任务上下文**:
- 开始时间: {datetime.fromtimestamp(task_context.start_time).strftime('%Y-%m-%d %H:%M:%S')}
- 已分配智能体: {task_context.assigned_agent or '无'}
- 执行结果: {len(task_context.agent_results)} 个结果

**🎯 强制执行的协调流程**:
1. **第一步**: 调用 `identify_task_type` 识别任务类型
2. **第二步**: 调用 `recommend_agent` 推荐最合适的智能体
3. **第三步**: 调用 `assign_task_to_agent` 分配任务给推荐智能体
4. **第四步**: 调用 `analyze_agent_result` 分析执行结果
5. **第五步**: 根据分析结果决定是否需要继续迭代

**⚠️ 重要提醒**:
- 必须严格按照上述流程执行，不得跳过任何步骤
- 推荐代理工具 `recommend_agent` 是必需的，不能直接调用 `assign_task_to_agent`
- 每次任务分配前都必须先调用推荐代理工具

{coordinator_tool_guide}

**执行要求**:
1. 严格按照上述工具使用指导进行操作
2. 绝对禁止直接调用智能体名称作为工具
3. 必须使用 assign_task_to_agent 工具来分配任务
4. 必须使用 recommend_agent 工具来推荐智能体
5. 按照推荐的协调流程执行

请根据用户需求和可用智能体能力，制定最优的执行策略并开始协调。
"""
    
    async def _tool_assign_task_to_agent(self, agent_id: str, task_description: str,
                                       expected_output: str = "",
                                       task_type: str = "composite",
                                       priority: str = "medium",
                                       design_file_path: str = None) -> Dict[str, Any]:
        """智能分配任务给最合适的智能体"""
        
        try:
            self.logger.info(f"🎯 分配任务给智能体: {agent_id}")
            self.logger.info(f"📋 任务描述: {task_description[:100]}...")
            
            # 检查智能体是否存在
            if agent_id not in self.registered_agents:
                return {
                    "success": False,
                    "error": f"智能体 {agent_id} 未注册",
                    "available_agents": list(self.registered_agents.keys())
                }
            
            agent_info = self.registered_agents[agent_id]
            agent = agent_info.agent_instance
            
            # 🔧 修复：添加智能体健康检查
            if hasattr(agent_info, 'failure_count') and agent_info.failure_count >= 3:
                return {
                    "success": False,
                    "error": f"智能体 {agent_id} 连续失败次数过多，已暂时禁用",
                    "agent_status": "disabled",
                    "failure_count": agent_info.failure_count
                }
            
            # 检查智能体状态
            if agent_info.status == AgentStatus.BUSY:
                return {
                    "success": False,
                    "error": f"智能体 {agent_id} 当前忙碌中",
                    "agent_status": agent_info.status.value
                }
            
            # 创建任务上下文
            task_id = f"task_{int(time.time())}"
            
            # 🎯 修复：TaskType验证过于死板的问题
            # 支持更多任务类型，包括"review"等
            try:
                task_type_enum = TaskType(task_type)
            except ValueError:
                # 如果task_type不在枚举中，映射到合适的类型
                task_type_mapping = {
                    "review": TaskType.VERIFICATION,
                    "test": TaskType.VERIFICATION,
                    "verify": TaskType.VERIFICATION,
                    "analyze": TaskType.ANALYSIS,
                    "debug": TaskType.DEBUG,
                    "design": TaskType.DESIGN,
                    "composite": TaskType.COMPOSITE
                }
                task_type_enum = task_type_mapping.get(task_type.lower(), TaskType.COMPOSITE)
                self.logger.info(f"🎯 任务类型映射: '{task_type}' -> {task_type_enum.value}")
            
            task_context = TaskContext(
                task_id=task_id,
                original_request=task_description,
                task_type=task_type_enum,
                priority=TaskPriority(priority),
                current_stage=f"assigned_to_{agent_id}",
                assigned_agent=agent_id,
                start_time=time.time()
            )
            
            # 🔧 修复：正确设置实验路径
            current_experiment_path = None
            
            # 1. 首先尝试从当前活跃任务中获取实验路径
            for task in self.active_tasks.values():
                if hasattr(task, 'experiment_path') and task.experiment_path:
                    current_experiment_path = task.experiment_path
                    self.logger.info(f"🧪 从活跃任务中获取实验路径: {current_experiment_path}")
                    break
            
            # 2. 如果没有找到，尝试从实验管理器获取
            if not current_experiment_path:
                try:
                    from core.experiment_manager import get_experiment_manager
                    exp_manager = get_experiment_manager()
                    
                    if exp_manager and exp_manager.current_experiment_path:
                        current_experiment_path = exp_manager.current_experiment_path
                        self.logger.info(f"🧪 从实验管理器获取实验路径: {current_experiment_path}")
                except (ImportError, Exception) as e:
                    self.logger.debug(f"实验管理器不可用: {e}")
            
            # 3. 如果还是没有找到，使用默认路径
            if not current_experiment_path:
                current_experiment_path = "./file_workspace"
                self.logger.warning(f"⚠️ 没有找到实验路径，使用默认路径: {current_experiment_path}")
            
            # 设置实验路径
            task_context.experiment_path = current_experiment_path
            self.logger.info(f"✅ 设置任务实验路径: {current_experiment_path}")
            
            # 🔧 新增：如果提供了 design_file_path，直接使用
            if design_file_path:
                task_context.design_file_path = design_file_path
                self.logger.info(f"📁 使用提供的设计文件路径: {design_file_path}")
            else:
                # 🔧 新增：尝试从之前的智能体结果中提取设计文件路径
                design_file_path = self._extract_design_file_path_from_previous_results()
                if design_file_path:
                    task_context.design_file_path = design_file_path
                    self.logger.info(f"📁 从之前结果中提取设计文件路径: {design_file_path}")
            
            # 检查是否是后续调用（通过对话历史判断）
            is_follow_up_call = False
            if hasattr(agent, 'conversation_history') and agent.conversation_history:
                # 检查对话历史中是否已经有相同的任务描述
                for msg in agent.conversation_history:
                    if msg.get("role") == "user" and "📋 协调智能体分配的任务" in msg.get("content", ""):
                        is_follow_up_call = True
                        break
            
            # 构建任务描述
            enhanced_task = self._build_enhanced_task_description(
                task_description=task_description,
                expected_output=expected_output,
                task_context=task_context,
                task_type=task_type,
                priority=priority,
                include_full_context=not is_follow_up_call  # 后续调用使用简化版本
            )
            
            # 更新智能体状态
            agent_info.status = AgentStatus.BUSY
            agent_info.last_used = time.time()
            agent_info.conversation_id = task_id
            
            # 记录任务分配
            self.active_tasks[task_id] = task_context
            task_context.agent_assignments.append({
                "agent_id": agent_id,
                "timestamp": time.time(),
                "task_description": task_description,
                "design_file_path": design_file_path,  # 🔧 新增：记录设计文件路径
                "experiment_path": current_experiment_path  # 🔧 新增：记录实验路径
            })
            
            self.logger.info(f"📤 发送任务给智能体 {agent_id}")
            self.logger.info(f"📋 任务描述: {enhanced_task[:200]}...")
            
            try:
                # 执行任务（调用智能体的Function Calling）
                start_time = time.time()
                
                # 🧠 添加上下文保持日志
                agent_conversation_summary = agent.get_conversation_summary() if hasattr(agent, 'get_conversation_summary') else {}
                self.logger.info(f"📋 调用前 agent 对话状态: {agent_conversation_summary}")
                
                # 🆕 设置任务上下文给智能体，用于对话历史记录
                if hasattr(agent, 'set_task_context'):
                    agent.set_task_context(task_context)
                    self.logger.info(f"🔗 已设置任务上下文给智能体 {agent_id}")
                
                # 🆕 记录任务分配到对话历史
                task_context.add_conversation_message(
                    role="system",
                    content=f"分配任务给智能体 {agent_id}: {task_description}",
                    agent_id=self.agent_id,
                    metadata={"type": "task_assignment", "target_agent": agent_id}
                )
                
                agent_response = await agent.process_with_function_calling(
                    user_request=enhanced_task,
                    conversation_id=task_id,
                    max_iterations=8
                )
                
                execution_time = time.time() - start_time
                
                # 更新智能体性能指标
                agent_info.total_execution_time += execution_time
                agent_info.average_response_time = agent_info.total_execution_time / (agent_info.success_count + agent_info.failure_count + 1)
                
                # 🔧 修复：更新成功计数
                agent_info.success_count += 1
                if hasattr(agent_info, 'failure_count'):
                    agent_info.failure_count = 0  # 重置失败计数
                
                # 🔧 检查响应质量，如果太短则请求详细总结
                enhanced_response = agent_response
                if len(agent_response.strip()) < 100:
                    self.logger.info(f"🔍 检测到智能体{agent_id}响应较短({len(agent_response)}字符)，请求详细总结...")
                    try:
                        # 请求智能体提供详细的工作总结
                        summary_request = f"""
请为刚才完成的任务提供一个详细的工作总结，包括：
1. 完成的主要工作和操作
2. 生成或修改的文件及其内容要点
3. 关键的技术选择和设计考虑
4. 任务的完成状态和结果

原始简短响应: {agent_response}
"""
                        summary_response = await agent.process_with_function_calling(
                            user_request=summary_request,
                            conversation_id=f"{task_id}_summary",
                            max_iterations=1
                        )
                        
                        if summary_response and len(summary_response) > len(agent_response):
                            enhanced_response = summary_response
                            self.logger.info(f"✅ 获得更详细的总结({len(summary_response)}字符)")
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ 获取详细总结失败: {e}")
                
                # 更新任务上下文
                task_context.agent_results[agent_id] = {
                    "response": enhanced_response,  # 使用增强的响应
                    "original_response": agent_response,  # 保留原始响应
                    "execution_time": execution_time,
                    "success": True,
                    "design_file_path": design_file_path,  # 🔧 新增：保存设计文件路径
                    "experiment_path": current_experiment_path  # 🔧 新增：保存实验路径
                }
                
                # 🆕 新增：将子智能体的增强响应保存到对话历史
                task_context.add_conversation_message(
                    role="assistant",
                    content=enhanced_response,  # 使用增强的响应
                    agent_id=agent_id,
                    metadata={
                        "type": "agent_response",
                        "task_id": task_id,
                        "execution_time": execution_time,
                        "response_length": len(str(enhanced_response)),
                        "original_response_length": len(str(agent_response))
                    }
                )
                
                # 🆕 数据收集用于Gradio可视化 - 智能体交互
                if hasattr(self, 'current_task_context') and self.current_task_context:
                    completion_timestamp = time.time()
                    self.current_task_context.agent_interactions.append({
                        "timestamp": completion_timestamp,
                        "coordinator_id": self.agent_id,
                        "target_agent_id": agent_id,
                        "task_description": task_description[:100] + ("..." if len(task_description) > 100 else ""),
                        "success": True,
                        "execution_time": execution_time,
                        "response_length": len(str(agent_response))
                    })
                    
                    # 记录工作流阶段
                    self.current_task_context.workflow_stages.append({
                        "timestamp": completion_timestamp,
                        "stage_name": f"task_completed_by_{agent_id}",
                        "description": f"任务由 {agent_id} 成功完成",
                        "agent_id": agent_id,
                        "duration": execution_time,
                        "success": True
                    })
                    
                    # 🆕 记录工作流阶段到TaskContext
                    if hasattr(self.current_task_context, 'add_workflow_stage'):
                        self.current_task_context.add_workflow_stage(
                            stage_name=f"agent_execution_{agent_id}",
                            description=f"智能体 {agent_id} 执行任务",
                            agent_id=agent_id,
                            duration=execution_time,
                            success=True,
                            metadata={
                                "task_type": task_type,
                                "priority": priority,
                                "response_length": len(str(agent_response))
                            }
                        )
                
                # 恢复智能体状态
                agent_info.status = AgentStatus.IDLE
                
                # 🆕 新增：记录任务完成状态
                task_context.add_conversation_message(
                    role="system",
                    content=f"任务协调完成，任务ID: {task_id}",
                    agent_id=self.agent_id,
                    metadata={"type": "task_completion", "success": True}
                )
                
                self.logger.info(f"✅ 智能体 {agent_id} 任务执行完成，耗时: {execution_time:.2f}秒")
                
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "task_id": task_id,
                    "response": agent_response,
                    "execution_time": execution_time,
                    "task_context": task_context,
                    "design_file_path": design_file_path,  # 🔧 新增：返回设计文件路径
                    "experiment_path": current_experiment_path  # 🔧 新增：返回实验路径
                }
                
            except Exception as e:
                # 恢复智能体状态
                agent_info.status = AgentStatus.IDLE
                agent_info.failure_count += 1
                agent_info.consecutive_failures += 1
                agent_info.consecutive_successes = 0
                agent_info.last_failure_time = time.time()
                
                error_msg = f"智能体 {agent_id} 执行任务失败: {str(e)}"
                self.logger.error(f"❌ {error_msg}")
                
                # 更新任务上下文
                task_context.error_history.append(error_msg)
                task_context.retry_count += 1
                
                # 🆕 数据收集用于Gradio可视化 - 智能体交互失败
                if hasattr(self, 'current_task_context') and self.current_task_context:
                    failure_timestamp = time.time()
                    self.current_task_context.agent_interactions.append({
                        "timestamp": failure_timestamp,
                        "coordinator_id": self.agent_id,
                        "target_agent_id": agent_id,
                        "task_description": task_description[:100] + ("..." if len(task_description) > 100 else ""),
                        "success": False,
                        "execution_time": time.time() - start_time,
                        "error": str(e)
                    })
                    
                    # 记录工作流阶段失败
                    self.current_task_context.workflow_stages.append({
                        "timestamp": failure_timestamp,
                        "stage_name": f"task_failed_by_{agent_id}",
                        "description": f"任务由 {agent_id} 执行失败",
                        "agent_id": agent_id,
                        "duration": time.time() - start_time,
                        "success": False,
                        "error": str(e)
                    })
                    
                    # 记录执行时间线
                    self.current_task_context.execution_timeline.append({
                        "timestamp": failure_timestamp,
                        "event_type": "agent_failure",
                        "agent_id": agent_id,
                        "description": f"{agent_id} 任务执行失败",
                        "details": {
                            "task_type": task_type,
                            "error": str(e),
                            "priority": priority
                        }
                    })
                
                return {
                    "success": False,
                    "agent_id": agent_id,
                    "task_id": task_id,
                    "error": error_msg,
                    "execution_time": time.time() - start_time
                }
                
        except Exception as e:
            error_msg = f"任务分配失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            # 🔧 修复：更新失败计数
            if agent_id in self.registered_agents:
                agent_info = self.registered_agents[agent_id]
                if not hasattr(agent_info, 'failure_count'):
                    agent_info.failure_count = 0
                agent_info.failure_count += 1
                self.logger.warning(f"⚠️ 智能体 {agent_id} 失败计数: {agent_info.failure_count}")
            
            return {
                "success": False,
                "error": error_msg
            }
    
    def _build_enhanced_task_description(self, task_description: str, 
                                       expected_output: str,
                                       task_context: TaskContext = None,
                                       task_type: str = "composite",
                                       priority: str = "medium",
                                       include_full_context: bool = True) -> str:
        """构建增强的任务描述"""
        
        # 🔧 修正1: 根据目标智能体过滤任务描述，移除Verilog智能体不应承担的测试台生成要求
        filtered_task_description = self._filter_task_description_by_agent(
            task_description, task_context.assigned_agent if task_context else "unknown"
        )
        
        # 构建外部testbench信息
        external_testbench_section = ""
        if task_context and hasattr(task_context, 'external_testbench_path') and task_context.external_testbench_path:
            external_testbench_section = f"""

**🎯 外部Testbench模式**:
- 外部testbench路径: {task_context.external_testbench_path}
- 工作指导: 如果你是代码审查智能体，请直接使用提供的testbench进行测试，不要生成新的testbench
- 专注任务: 代码审查、错误修复、测试执行和结果分析"""
        
        # 🔧 新增：构建设计文件路径信息
        design_file_section = ""
        if task_context and hasattr(task_context, 'design_file_path') and task_context.design_file_path:
            design_file_section = f"""

**📁 设计文件路径**:
- 设计文件: {task_context.design_file_path}
- 工作指导: 请直接使用此路径的设计文件进行代码审查和测试台生成
- 重要提示: 这是需要审查的具体文件路径，请优先使用此文件"""
          
        # 构建实验路径信息 - 从任务上下文或获取当前实验路径
        experiment_path_section = ""
        current_experiment_path = None
        
        if task_context and hasattr(task_context, 'experiment_path') and task_context.experiment_path:
            current_experiment_path = task_context.experiment_path
            self.logger.info(f"🧪 使用任务上下文中的实验路径: {current_experiment_path}")
        else:
            # 尝试从活跃任务中获取实验路径
            for task in self.active_tasks.values():
                if hasattr(task, 'experiment_path') and task.experiment_path:
                    current_experiment_path = task.experiment_path
                    self.logger.info(f"🧪 从活跃任务中获取实验路径: {current_experiment_path}")
                    break
            
            # 如果没有找到，则使用默认的文件工作空间路径
            if not current_experiment_path:
                current_experiment_path = "./file_workspace"
                self.logger.warning(f"⚠️ 没有找到实验路径，使用默认路径: {current_experiment_path}")
        
        if current_experiment_path:
            experiment_path_section = f"""

**📁 实验文件路径**:
- 当前实验路径: {current_experiment_path}
- 设计文件保存: {current_experiment_path}/designs/
- 测试台保存: {current_experiment_path}/testbenches/
- 报告保存: {current_experiment_path}/reports/
- 临时文件: {current_experiment_path}/temp/

**⚠️ 重要文件管理要求**:
1. 所有生成的Verilog代码必须保存为.v文件
2. 设计模块保存到designs目录，测试台保存到testbenches目录
3. 文档和报告保存到reports目录
4. 必须在任务总结中返回所有生成文件的完整路径
5. 文件命名应该清晰，避免重复和冲突"""
        
        # 根据智能体类型添加专用的工具使用指导
        agent_tool_guide = self._get_agent_specific_tool_guide(task_context.assigned_agent if task_context else "unknown")
        
        # 根据include_full_context参数决定是否包含完整上下文
        if include_full_context:
            enhanced_task = f"""
📋 协调智能体分配的任务

**任务描述**:
{filtered_task_description}

**期望输出**:
{expected_output if expected_output else "根据任务描述生成相应的代码和文档"}

**任务类型**:
- 类型: {task_type}
- 优先级: {priority}

**任务上下文**:
- 任务ID: {task_context.task_id if task_context else "unknown"}
- 当前阶段: {task_context.current_stage if task_context else "initial"}
- 迭代次数: {task_context.iteration_count if task_context else 0}
{external_testbench_section}
{design_file_section}
{experiment_path_section}

{agent_tool_guide}

**执行要求**:
1. 仔细分析任务需求
2. 根据上述工具指导选择合适的工具
3. 生成高质量的代码并保存为文件
4. 提供详细的说明文档
5. 确保代码可读性和可维护性
6. **强制要求**: 在任务完成后，在响应中明确列出所有生成文件的路径

请开始执行任务，严格按照工具使用指导进行操作。
"""
        else:
            # 简化版本，只包含核心任务描述
            enhanced_task = f"""
📋 继续执行任务

**当前任务**: {filtered_task_description}
{design_file_section}

{agent_tool_guide}

**执行要求**:
1. 继续之前的任务执行
2. 根据上述工具指导选择合适的工具
3. 生成高质量的代码并保存为文件
4. 提供详细的说明文档
5. 确保代码可读性和可维护性
6. **强制要求**: 在任务完成后，在响应中明确列出所有生成文件的路径

请继续执行任务，严格按照工具使用指导进行操作。
"""
        
        return enhanced_task
    
    def _filter_task_description_by_agent(self, task_description: str, agent_id: str) -> str:
        """根据目标智能体过滤任务描述，移除不合适的要求"""
        
        if agent_id == "enhanced_real_verilog_agent":
            # 🔧 修正: 为Verilog设计智能体移除测试台生成相关要求 - 使用更直接的方法
            original_desc = task_description
            
            # 🔧 方法1: 直接字符串替换，移除常见的测试台相关表述
            filtered_desc = task_description
            
            # 移除常见的测试台相关短语
            testbench_phrases = [
                "和测试台",
                "、测试台", 
                "以及测试台",
                "还有测试台",
                "包含测试台",
                "生成测试台",
                "创建测试台",
                "编写测试台"
            ]
            
            for phrase in testbench_phrases:
                filtered_desc = filtered_desc.replace(phrase, "")
            
            # 🔧 方法2: 使用正则表达式清理
            import re
            testbench_patterns = [
                r"，包含完整的端口定义、功能实现和测试台",
                r"包含完整的端口定义、功能实现和测试台",
                r"生成.*?测试台.*?进行验证",
                r"并.*?生成.*?测试台",
                r"以及.*?测试台",
                r"和.*?测试台", 
                r"、.*?测试台"
            ]
            
            for pattern in testbench_patterns:
                filtered_desc = re.sub(pattern, "", filtered_desc, flags=re.IGNORECASE)
            
            # 🔧 方法3: 清理多余的标点符号
            filtered_desc = re.sub(r"，\s*$", "", filtered_desc)  # 移除末尾逗号
            filtered_desc = re.sub(r"、\s*$", "", filtered_desc)  # 移除末尾顿号
            filtered_desc = re.sub(r"和\s*$", "", filtered_desc)  # 移除末尾"和"
            filtered_desc = filtered_desc.strip()
            
            # 检查是否原来包含测试台要求
            has_testbench_requirement = ("测试台" in original_desc or 
                                       "testbench" in original_desc.lower() or 
                                       "验证" in original_desc)
            
            # 如果原来包含测试台要求，添加明确的职责说明
            if has_testbench_requirement:
                if filtered_desc:
                    filtered_desc += """

🚨 **重要说明**: 
- 本任务仅要求完成Verilog模块设计和代码生成
- 测试台(testbench)生成和验证工作将由后续的代码审查智能体负责
- 请专注于设计模块的端口定义、功能实现和代码质量"""
                else:
                    # 如果过滤后为空，提供默认的设计任务描述
                    filtered_desc = """设计Verilog模块，专注于模块架构和功能实现

🚨 **重要说明**: 
- 本任务仅要求完成Verilog模块设计和代码生成
- 测试台(testbench)生成和验证工作将由后续的代码审查智能体负责
- 请专注于设计模块的端口定义、功能实现和代码质量"""
            
            return filtered_desc.strip()
        
        elif agent_id == "enhanced_real_code_review_agent":
            # 代码审查智能体保持原始任务描述
            return task_description
        
        else:
            # 未知智能体类型，保持原始描述
            return task_description
    
    def _get_agent_specific_tool_guide(self, agent_id: str) -> str:
        """根据智能体类型获取专用的工具使用指导"""
        
        if agent_id == "enhanced_real_verilog_agent":
            return """
**🛠️ EnhancedRealVerilogAgent 专用工具使用指导**

📋 **可用工具列表**:

🚨 **重要提醒**: 本智能体专注于Verilog模块设计，**绝不负责测试台(testbench)生成**

### 1. **analyze_design_requirements** - 设计需求分析
   **功能**: 分析和解析Verilog设计需求，提取关键设计参数
   **参数**:
   - `requirements` (必填, string): 设计需求描述，包含功能规格和约束条件
   - `design_type` (可选, string): 设计类型，可选值: "combinational", "sequential", "mixed", "custom"，默认"mixed"
   - `complexity_level` (可选, string): 设计复杂度级别，可选值: "simple", "medium", "complex", "advanced"，默认"medium"
   **调用示例**:
   ```json
   {
       "tool_name": "analyze_design_requirements",
       "parameters": {
           "requirements": "设计一个名为counter的Verilog模块",
           "design_type": "sequential",
           "complexity_level": "medium"
       }
   }
   ```

### 2. **generate_verilog_code** - Verilog代码生成
   **功能**: 生成高质量的Verilog HDL代码
   **参数**:
   - `module_name` (必填, string): 模块名称
   - `requirements` (必填, string): 设计需求和功能描述
   - `input_ports` (必填, array): 输入端口列表，格式: [{"name": "端口名", "width": 位宽, "type": "类型"}]
   - `output_ports` (必填, array): 输出端口列表，格式同上
   - `coding_style` (可选, string): 编码风格，可选值: "rtl", "behavioral", "structural"，默认"rtl"
   **调用示例**:
   ```json
   {
       "tool_name": "generate_verilog_code",
       "parameters": {
           "module_name": "counter",
           "requirements": "4位计数器，支持复位和使能",
           "input_ports": [
               {"name": "clk", "width": 1, "type": "input"},
               {"name": "rst_n", "width": 1, "type": "input"},
               {"name": "en", "width": 1, "type": "input"}
           ],
           "output_ports": [
               {"name": "count", "width": 4, "type": "output"}
           ],
           "coding_style": "rtl"
       }
   }
   ```

### 3. **analyze_code_quality** - 代码质量分析
   **功能**: 分析Verilog代码质量，提供详细的评估报告
   **参数**:
   - `verilog_code` (必填, string): 要分析的Verilog代码
   - `module_name` (必填, string): 模块名称
   **调用示例**:
   ```json
   {
       "tool_name": "analyze_code_quality",
       "parameters": {
           "verilog_code": "module counter(...); ... endmodule",
           "module_name": "counter"
       }
   }
   ```

### 5. **optimize_verilog_code** - 代码优化
   **功能**: 优化Verilog代码，支持面积、速度、功耗等优化目标
   **参数**:
   - `verilog_code` (必填, string): 要优化的Verilog代码
   - `optimization_target` (必填, string): 优化目标，可选值: "area", "speed", "power", "timing"
   - `module_name` (必填, string): 模块名称
   **调用示例**:
   ```json
   {
       "tool_name": "optimize_verilog_code",
       "parameters": {
           "verilog_code": "module counter(...); ... endmodule",
           "optimization_target": "area",
           "module_name": "counter"
       }
   }
   ```

⭐ **推荐执行流程**:
1. analyze_design_requirements → 2. generate_verilog_code → 3. analyze_code_quality 
→ 4. optimize_verilog_code (可选)

💡 **职责边界**: 
- ✅ 负责: Verilog模块设计、端口定义、功能实现、代码生成
- ❌ 禁止: 测试台(testbench)生成、仿真验证、测试执行
- 📝 说明: 测试台和验证工作由代码审查智能体(enhanced_real_code_review_agent)专门负责
"""

        elif agent_id == "enhanced_real_code_review_agent":
            return """
**🛠️ EnhancedRealCodeReviewAgent 专用工具使用指导**

📋 **可用工具列表**:

### 1. **generate_testbench** - 测试台生成
   **功能**: 为Verilog模块生成全面的测试台(testbench)
   **参数**:
   - `module_name` (必填, string): 目标模块名称
   - `module_code` (必填, string): 目标模块代码 (也可使用 `code`, `design_code`)
   - `test_scenarios` (可选, array): 测试场景列表 (也可使用 `test_cases`)
   - `clock_period` (可选, number): 时钟周期(ns)，范围0.1-1000.0，默认10.0
   - `simulation_time` (可选, integer): 仿真时间，范围100-1000000，默认10000
   **调用示例**:
   ```json
   {
       "tool_name": "generate_testbench",
       "parameters": {
           "module_name": "counter",
           "module_code": "module counter(...); ... endmodule",
           "test_scenarios": [
               {"name": "basic_test", "description": "基本功能验证"},
               {"name": "reset_test", "description": "复位功能测试"}
           ],
           "clock_period": 10.0,
           "simulation_time": 10000
       }
   }
   ```

### 2. **run_simulation** - 仿真执行
   **功能**: 使用专业工具运行Verilog仿真和验证
   **参数**:
   - `module_file` 或 `module_code` (必填): 模块文件路径或代码内容
   - `testbench_file` 或 `testbench_code` (必填): 测试台文件路径或代码内容
   - `simulator` (可选, string): 仿真器类型，可选值: "iverilog", "modelsim", "vivado", "auto"，默认"iverilog"
   - `simulation_options` (可选, object): 仿真选项配置
   **调用示例**:
   ```json
   {
       "tool_name": "run_simulation",
       "parameters": {
           "module_file": "counter.v",
           "testbench_file": "testbench_counter.v",
           "simulator": "iverilog",
           "simulation_options": {"timescale": "1ns/1ps"}
       }
   }
   ```

### 3. **use_external_testbench** - 外部测试台使用
   **功能**: 使用外部提供的testbench文件进行测试验证
   **参数**:
   - `design_code` (必填, string): 设计代码
   - `external_testbench_path` (必填, string): 外部testbench文件路径
   - `design_module_name` (必填, string): 设计模块名称
   - `simulator` (可选, string): 仿真器类型，默认"iverilog"
   **调用示例**:
   ```json
   {
       "tool_name": "use_external_testbench",
       "parameters": {
           "design_code": "module counter(...); ... endmodule",
           "external_testbench_path": "./testbenches/counter_tb.v",
           "design_module_name": "counter",
           "simulator": "iverilog"
       }
   }
   ```

### 4. **generate_build_script** - 构建脚本生成
   **功能**: 生成专业的构建脚本(Makefile或shell脚本)
   **参数**:
   - `verilog_files` (必填, array): Verilog文件列表 (也可使用 `design_files`)
   - `testbench_files` (必填, array): 测试台文件列表
   - `script_type` (可选, string): 脚本类型，可选值: "makefile", "bash", "tcl", "python"，默认"makefile"
   - `target_name` (可选, string): 目标名称，默认"simulation"
   - `build_options` (可选, object): 构建选项配置
   **调用示例**:
   ```json
   {
       "tool_name": "generate_build_script",
       "parameters": {
           "verilog_files": ["counter.v"],
           "testbench_files": ["testbench_counter.v"],
           "script_type": "makefile",
           "target_name": "simulation",
           "build_options": {"simulator": "iverilog"}
       }
   }
   ```

### 5. **execute_build_script** - 脚本执行
   **功能**: 安全执行构建脚本进行编译和仿真
   **参数**:
   - `script_name` (必填, string): 脚本文件名
   - `action` (可选, string): 执行动作，可选值: "all", "compile", "simulate", "clean"，默认"all"
   - `arguments` (可选, array): 附加参数列表
   - `timeout` (可选, integer): 超时时间(秒)，默认300
   - `working_directory` (可选, string): 工作目录
   **调用示例**:
   ```json
   {
       "tool_name": "execute_build_script",
       "parameters": {
           "script_name": "Makefile",
           "action": "all",
           "timeout": 300,
           "working_directory": "./file_workspace"
       }
   }
   ```

### 6. **analyze_test_failures** - 测试失败分析
   **功能**: 分析测试失败原因并提供具体修复建议
   **参数**:
   - `design_code` (必填, string): 需要分析的设计代码
   - `compilation_errors` (可选, string): 编译错误输出
   - `simulation_errors` (可选, string): 仿真错误输出
   - `test_assertions` (可选, string): 测试断言失败信息
   - `testbench_code` (可选, string): 测试台代码
   - `iteration_number` (可选, integer): 当前TDD迭代次数
   - `previous_fixes` (可选, array): 之前尝试的修复方法
   **调用示例**:
   ```json
   {
       "tool_name": "analyze_test_failures",
       "parameters": {
           "design_code": "module counter(...); ... endmodule",
           "compilation_errors": "Error: undefined signal 'clk'",
           "simulation_errors": "simulation failed at time 100ns",
           "testbench_code": "module testbench; ... endmodule",
           "iteration_number": 1
       }
   }
   ```

⭐ **推荐执行流程**:
1. generate_testbench → 2. run_simulation → 3. analyze_test_failures (如有问题) 
→ 4. generate_build_script → 5. execute_build_script → 6. use_external_testbench (如有外部测试台)

💡 **重要提示**: 专注于代码审查、测试和验证，不负责Verilog设计
"""

        elif agent_id in ["llm_coordinator_agent", "coordinator", "unknown"]:
            # 对于LLMCoordinatorAgent或其他agent，返回协调工具指导
            return """
**🛠️ LLMCoordinatorAgent 协调工具使用指导**

📋 **可用工具列表**:

### 1. **assign_task_to_agent** - 智能任务分配
   **功能**: 将任务分配给最合适的智能体
   **参数**:
   - `agent_id` (必填, string): 智能体ID，可选值: "enhanced_real_verilog_agent", "enhanced_real_code_review_agent"
   - `task_description` (必填, string): 详细的任务描述
   - `expected_output` (可选, string): 期望的输出格式，默认空字符串
   - `task_type` (可选, string): 任务类型，可选值: "design", "review", "composite"，默认"design"
   - `priority` (可选, string): 任务优先级，可选值: "low", "medium", "high"，默认"medium"
   **调用示例**:
   ```json
   {
       "tool_name": "assign_task_to_agent",
       "parameters": {
           "agent_id": "enhanced_real_verilog_agent",
           "task_description": "设计一个名为counter的Verilog模块",
           "expected_output": "生成完整的Verilog代码文件",
           "task_type": "design",
           "priority": "medium"
       }
   }
   ```

### 2. **analyze_agent_result** - 结果质量分析
   **功能**: 分析智能体执行结果的质量和完整性
   **参数**:
   - `agent_id` (必填, string): 智能体ID
   - `result` (必填, object): 智能体返回的结果数据
   - `task_context` (可选, object): 任务上下文信息，默认{}
   - `quality_threshold` (可选, number): 质量阈值，范围0-100，默认80.0
   **调用示例**:
   ```json
   {
       "tool_name": "analyze_agent_result",
       "parameters": {
           "agent_id": "enhanced_real_verilog_agent",
           "result": {"status": "success", "generated_files": ["counter.v"]},
           "task_context": {"task_id": "task_001"},
           "quality_threshold": 80.0
       }
   }
   ```

### 3. **check_task_completion** - 任务完成检查
   **功能**: 检查任务是否已完成并符合要求
   **参数**:
   - `task_id` (必填, string): 任务标识符
   - `all_results` (必填, array): 所有相关结果列表
   - `original_requirements` (必填, string): 原始需求描述
   - `completion_criteria` (可选, object): 完成标准，默认{}
   **调用示例**:
   ```json
   {
       "tool_name": "check_task_completion",
       "parameters": {
           "task_id": "task_001",
           "all_results": [{"status": "success", "files": ["counter.v"]}],
           "original_requirements": "设计一个名为counter的Verilog模块",
           "completion_criteria": {"require_testbench": true}
       }
   }
   ```

### 4. **query_agent_status** - 智能体状态查询
   **功能**: 查询智能体的当前状态和性能信息
   **参数**:
   - `agent_id` (必填, string): 智能体ID
   - `include_performance` (可选, boolean): 是否包含性能数据，默认true
   - `include_history` (可选, boolean): 是否包含历史记录，默认false
   **调用示例**:
   ```json
   {
       "tool_name": "query_agent_status",
       "parameters": {
           "agent_id": "enhanced_real_verilog_agent",
           "include_performance": true,
           "include_history": false
       }
   }
   ```

### 5. **identify_task_type** - 任务类型识别
   **功能**: 识别和分类用户任务的类型
   **参数**:
   - `user_request` (必填, string): 用户的原始请求
   - `context` (可选, object): 上下文信息，默认{}
   **调用示例**:
   ```json
   {
       "tool_name": "identify_task_type",
       "parameters": {
           "user_request": "设计一个名为counter的Verilog模块",
           "context": {}
       }
   }
   ```

### 6. **recommend_agent** - 智能体推荐
   **功能**: 基于任务类型推荐最合适的智能体
   **参数**:
   - `task_type` (必填, string): 任务类型
   - `task_description` (必填, string): 任务描述
   - `priority` (可选, string): 优先级，可选值: "low", "medium", "high"，默认"medium"
   - `constraints` (可选, object): 约束条件，默认null
   **调用示例**:
   ```json
   {
       "tool_name": "recommend_agent",
       "parameters": {
           "task_type": "design",
           "task_description": "设计一个名为counter的Verilog模块",
           "priority": "medium",
           "constraints": {}
       }
   }
   ```

### 7. **provide_final_answer** - 最终答案提供
   **功能**: 提供任务执行的最终答案和总结
   **参数**:
   - `final_summary` (必填, string): 最终总结
   - `task_status` (必填, string): 任务状态，可选值: "success", "partial", "failed"
   - `results_summary` (可选, object): 结果摘要，默认{}
   **调用示例**:
   ```json
   {
       "tool_name": "provide_final_answer",
       "parameters": {
           "final_summary": "成功设计并生成了counter模块",
           "task_status": "success",
           "results_summary": {"generated_files": ["counter.v", "counter_tb.v"]}
       }
   }
   ```

⭐ **推荐协调流程**:
1. identify_task_type → 2. recommend_agent → 3. assign_task_to_agent 
→ 4. analyze_agent_result → 5. check_task_completion → 6. provide_final_answer

💡 **重要提示**: 作为协调者，主要负责任务分配和结果分析
"""
        
        else:
            # 未知agent类型，返回通用指导
            return """
**🛠️ 通用工具使用指导**

⚠️ **重要提示**: 未识别的智能体类型，请确保使用正确的工具调用方式。

📋 **基本原则**:
- 严格按照工具的JSON schema调用
- 确保参数类型和格式正确
- 避免调用不存在的工具
- 详细阅读工具描述和参数说明

如需获取具体的工具使用指导，请调用 get_tool_usage_guide 工具。
"""
    
    async def _tool_analyze_agent_result(self, agent_id: str, result: Dict[str, Any],
                                       task_context: Dict[str, Any] = None,
                                       quality_threshold: float = 80.0) -> Dict[str, Any]:
        """增强的智能体执行结果分析"""
        
        try:
            self.logger.info(f"🔍 深度分析智能体 {agent_id} 的执行结果")
            
            # 🔧 修复：确保 result 参数是字典类型
            if result is None:
                result = {}
            elif isinstance(result, str):
                # 如果是字符串，尝试解析为字典
                try:
                    import json
                    result = json.loads(result)
                except:
                    result = {"raw_response": result}
            
            # 更新智能体性能指标
            self._update_agent_performance(agent_id, result)
            
            # 深度分析结果质量
            analysis = self._enhanced_result_quality_analysis(result, task_context, quality_threshold)
            
            # 确定下一步行动
            next_action = self._determine_enhanced_next_action(analysis, task_context)
            
            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(analysis, agent_id)
            
            return {
                "success": True,
                "analysis": analysis,
                "next_action": next_action,
                "improvement_suggestions": improvement_suggestions,
                "agent_id": agent_id,
                "quality_threshold": quality_threshold
            }
            
        except Exception as e:
            self.logger.error(f"❌ 结果分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }
    
    def _update_agent_performance(self, agent_id: str, result: Dict[str, Any]):
        """更新智能体性能指标"""
        if agent_id not in self.registered_agents:
            return
        
        agent_info = self.registered_agents[agent_id]
        
        # 更新执行时间
        execution_time = result.get("execution_time", 0)
        if execution_time > 0:
            agent_info.total_execution_time += execution_time
            total_tasks = agent_info.success_count + agent_info.failure_count
            if total_tasks > 0:
                agent_info.average_response_time = agent_info.total_execution_time / total_tasks
        
        # 更新成功/失败统计
        if result.get("success", False):
            agent_info.success_count += 1
            agent_info.last_success_time = time.time()
            agent_info.consecutive_successes += 1
            agent_info.consecutive_failures = 0
        else:
            agent_info.failure_count += 1
            agent_info.last_failure_time = time.time()
            agent_info.consecutive_failures += 1
            agent_info.consecutive_successes = 0
    
    def _enhanced_result_quality_analysis(self, result: Dict[str, Any], 
                                        task_context: Dict[str, Any],
                                        quality_threshold: float) -> Dict[str, Any]:
        """增强的结果质量分析 - 包含文件验证、实际执行检查和代码测试流程检查"""
        
        analysis = {
            "quality_score": 0.0,
            "completeness": "unknown",
            "issues": [],
            "strengths": [],
            "recommendations": [],
            "detailed_metrics": {},
            "risk_assessment": "low",
            "file_verification": {},
            "actual_execution_check": {},
            "code_testing_workflow": {}
        }
        
        # 检查结果是否为空
        if not result or not result.get("success", False):
            analysis["completeness"] = "failed"
            analysis["issues"].append("任务执行失败")
            analysis["recommendations"].append("重新分配任务或更换智能体")
            analysis["risk_assessment"] = "high"
            return analysis
        
        # 获取原始任务需求
        original_request = task_context.get("original_request", "") if task_context else ""
        
        # 分析结果内容
        result_content = result.get("result", "") if isinstance(result.get("result"), str) else str(result.get("result", ""))
        if not result_content:
            analysis["completeness"] = "incomplete"
            analysis["issues"].append("结果内容为空")
            analysis["recommendations"].append("要求智能体重新执行并提供详细结果")
            analysis["risk_assessment"] = "medium"
            return analysis
        
        # 执行文件验证、实际执行检查和代码测试流程检查
        file_verification = self._verify_file_generation(result_content, original_request)
        execution_check = self._check_actual_execution(result_content, original_request)
        testing_workflow = self._check_code_testing_workflow(result_content, original_request, task_context)
        
        analysis["file_verification"] = file_verification
        analysis["actual_execution_check"] = execution_check
        analysis["code_testing_workflow"] = testing_workflow
        
        # 详细质量指标分析
        detailed_metrics = self._analyze_detailed_metrics(result_content, result, file_verification, execution_check)
        analysis["detailed_metrics"] = detailed_metrics
        
        # 计算综合质量分数（包含实际执行和测试流程权重）
        quality_score = self._calculate_comprehensive_quality_score(detailed_metrics, file_verification, execution_check, testing_workflow)
        analysis["quality_score"] = quality_score
        
        # 分析问题和优势
        analysis["issues"] = self._identify_quality_issues(detailed_metrics, file_verification, execution_check, testing_workflow, original_request)
        analysis["strengths"] = self._identify_quality_strengths(detailed_metrics, file_verification, execution_check, testing_workflow)
        
        # 根据质量分数、实际执行情况和测试流程完整性判断完整性
        if not file_verification.get("all_required_files_generated", False):
            analysis["completeness"] = "incomplete"
            analysis["risk_assessment"] = "high"
            analysis["issues"].append("未实际生成所需文件")
        elif not execution_check.get("simulation_actually_executed", False) and "测试台" in original_request:
            analysis["completeness"] = "incomplete" 
            analysis["risk_assessment"] = "high"
            analysis["issues"].append("未实际执行仿真验证")
        elif testing_workflow.get("workflow_completeness", 0) < 50 and ("测试" in original_request or "验证" in original_request):
            analysis["completeness"] = "incomplete"
            analysis["risk_assessment"] = "high"
            analysis["issues"].append("代码测试流程不完整")
        elif quality_score >= quality_threshold:
            analysis["completeness"] = "complete"
            analysis["risk_assessment"] = "low"
        elif quality_score >= quality_threshold * 0.7:
            analysis["completeness"] = "partial"
            analysis["risk_assessment"] = "medium"
        else:
            analysis["completeness"] = "incomplete"
            analysis["risk_assessment"] = "high"
        
        # 生成具体建议
        analysis["recommendations"] = self._generate_enhanced_recommendations(
            detailed_metrics, quality_score, quality_threshold, 
            file_verification, execution_check, testing_workflow, original_request
        )
        
        return analysis
    
    def _verify_file_generation(self, result_content: str, original_request: str) -> Dict[str, Any]:
        """验证是否实际生成了所需文件"""
        verification = {
            "verilog_file_mentioned": False,
            "testbench_file_mentioned": False,
            "files_actually_written": False,
            "all_required_files_generated": False,
            "missing_files": []
        }
        
        # 检查是否提到了Verilog文件
        if ".v" in result_content or "module" in result_content.lower():
            verification["verilog_file_mentioned"] = True
        
        # 检查是否提到了测试台文件
        if ("testbench" in result_content.lower() or "tb_" in result_content.lower() or 
            "_tb.v" in result_content or "test" in result_content.lower()):
            verification["testbench_file_mentioned"] = True
        
        # 检查是否实际执行了文件写入操作
        # 通过检查是否有工具调用的迹象
        if ("write_file" in result_content.lower() or 
            "文件已生成" in result_content or "文件创建" in result_content or
            "保存到" in result_content or "写入文件" in result_content):
            verification["files_actually_written"] = True
        
        # 分析原始需求，确定需要的文件
        required_files = []
        if "verilog" in original_request.lower() or "模块" in original_request:
            required_files.append("verilog_module")
        if ("测试台" in original_request or "testbench" in original_request.lower() or 
            "验证" in original_request or "test" in original_request.lower()):
            required_files.append("testbench")
        
        # 检查所有必需文件是否都生成了
        missing_files = []
        if "verilog_module" in required_files and not verification["verilog_file_mentioned"]:
            missing_files.append("Verilog模块文件")
        if "testbench" in required_files and not verification["testbench_file_mentioned"]:
            missing_files.append("测试台文件")
        
        verification["missing_files"] = missing_files
        verification["all_required_files_generated"] = (len(missing_files) == 0 and 
                                                       verification["files_actually_written"])
        
        return verification
    
    def _check_actual_execution(self, result_content: str, original_request: str) -> Dict[str, Any]:
        """检查是否实际执行了所需操作"""
        execution_check = {
            "simulation_mentioned": False,
            "simulation_actually_executed": False,
            "tools_called": False,
            "concrete_results_provided": False,
            "missing_executions": []
        }
        
        # 检查是否提到了仿真
        if ("仿真" in result_content or "simulation" in result_content.lower() or 
            "run_simulation" in result_content or "执行仿真" in result_content):
            execution_check["simulation_mentioned"] = True
        
        # 检查是否实际执行了仿真（通过具体输出判断）
        if (("仿真结果" in result_content or "simulation result" in result_content.lower() or
             "波形" in result_content or "waveform" in result_content.lower() or
             "仿真输出" in result_content or "时序" in result_content) and 
            execution_check["simulation_mentioned"]):
            execution_check["simulation_actually_executed"] = True
        
        # 检查是否调用了工具
        if ("工具调用" in result_content or "tool_call" in result_content.lower() or
            "执行工具" in result_content or "function calling" in result_content.lower()):
            execution_check["tools_called"] = True
        
        # 检查是否提供了具体结果
        if ("执行成功" in result_content and "结果" in result_content) or "输出:" in result_content:
            execution_check["concrete_results_provided"] = True
        
        # 分析缺失的执行项
        missing_executions = []
        if ("测试台" in original_request or "验证" in original_request) and not execution_check["simulation_actually_executed"]:
            missing_executions.append("仿真验证执行")
        if ("文件" in original_request or "生成" in original_request) and not execution_check["tools_called"]:
            missing_executions.append("文件生成操作")
        
        execution_check["missing_executions"] = missing_executions
        
        return execution_check
    
    def _check_code_testing_workflow(self, result_content: str, original_request: str, task_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """专门检查代码测试流程的完整性"""
        testing_workflow = {
            "test_plan_created": False,
            "test_cases_designed": False,
            "testbench_generated": False,
            "simulation_executed": False,
            "test_results_analyzed": False,
            "coverage_analysis_performed": False,
            "test_report_generated": False,
            "workflow_completeness": 0.0,
            "missing_testing_steps": [],
            "testing_quality_score": 0.0,
            "test_coverage_metrics": {},
            "test_execution_details": {}
        }
        
        # 1. 检查测试计划创建
        test_plan_indicators = [
            "测试计划", "test plan", "测试策略", "test strategy", 
            "测试目标", "test objectives", "测试范围", "test scope"
        ]
        if any(indicator in result_content for indicator in test_plan_indicators):
            testing_workflow["test_plan_created"] = True
        
        # 2. 检查测试用例设计
        test_case_indicators = [
            "测试用例", "test case", "测试向量", "test vector",
            "边界测试", "boundary test", "功能测试", "functional test",
            "时序测试", "timing test", "异常测试", "exception test"
        ]
        if any(indicator in result_content for indicator in test_case_indicators):
            testing_workflow["test_cases_designed"] = True
        
        # 3. 检查测试台生成
        testbench_indicators = [
            "testbench", "测试台", "tb_", "_tb.v", "initial", "always",
            "test stimulus", "测试激励", "时钟生成", "clock generation"
        ]
        if any(indicator in result_content for indicator in testbench_indicators):
            testing_workflow["testbench_generated"] = True
        
        # 4. 检查仿真执行
        simulation_indicators = [
            "仿真执行", "simulation executed", "仿真结果", "simulation result",
            "波形输出", "waveform output", "仿真完成", "simulation completed",
            "仿真时间", "simulation time", "仿真周期", "simulation cycles"
        ]
        if any(indicator in result_content for indicator in simulation_indicators):
            testing_workflow["simulation_executed"] = True
        
        # 5. 检查测试结果分析
        result_analysis_indicators = [
            "测试结果分析", "test result analysis", "结果验证", "result verification",
            "功能正确性", "functional correctness", "时序正确性", "timing correctness",
            "测试通过", "test passed", "测试失败", "test failed"
        ]
        if any(indicator in result_content for indicator in result_analysis_indicators):
            testing_workflow["test_results_analyzed"] = True
        
        # 6. 检查覆盖率分析
        coverage_indicators = [
            "代码覆盖率", "code coverage", "功能覆盖率", "functional coverage",
            "分支覆盖率", "branch coverage", "语句覆盖率", "statement coverage",
            "覆盖率报告", "coverage report", "覆盖率统计", "coverage statistics"
        ]
        if any(indicator in result_content for indicator in coverage_indicators):
            testing_workflow["coverage_analysis_performed"] = True
        
        # 7. 检查测试报告生成
        report_indicators = [
            "测试报告", "test report", "测试总结", "test summary",
            "测试结论", "test conclusion", "测试建议", "test recommendations"
        ]
        if any(indicator in result_content for indicator in report_indicators):
            testing_workflow["test_report_generated"] = True
        
        # 计算工作流完整性
        completed_steps = sum([
            testing_workflow["test_plan_created"],
            testing_workflow["test_cases_designed"],
            testing_workflow["testbench_generated"],
            testing_workflow["simulation_executed"],
            testing_workflow["test_results_analyzed"],
            testing_workflow["coverage_analysis_performed"],
            testing_workflow["test_report_generated"]
        ])
        testing_workflow["workflow_completeness"] = (completed_steps / 7.0) * 100
        
        # 识别缺失的测试步骤
        missing_steps = []
        if not testing_workflow["test_plan_created"]:
            missing_steps.append("测试计划创建")
        if not testing_workflow["test_cases_designed"]:
            missing_steps.append("测试用例设计")
        if not testing_workflow["testbench_generated"]:
            missing_steps.append("测试台生成")
        if not testing_workflow["simulation_executed"]:
            missing_steps.append("仿真执行")
        if not testing_workflow["test_results_analyzed"]:
            missing_steps.append("测试结果分析")
        if not testing_workflow["coverage_analysis_performed"]:
            missing_steps.append("覆盖率分析")
        if not testing_workflow["test_report_generated"]:
            missing_steps.append("测试报告生成")
        
        testing_workflow["missing_testing_steps"] = missing_steps
        
        # 计算测试质量分数
        quality_factors = {
            "test_plan_created": 15,
            "test_cases_designed": 20,
            "testbench_generated": 25,
            "simulation_executed": 20,
            "test_results_analyzed": 10,
            "coverage_analysis_performed": 5,
            "test_report_generated": 5
        }
        
        quality_score = sum([
            quality_factors[step] for step, completed in testing_workflow.items() 
            if step in quality_factors and completed
        ])
        testing_workflow["testing_quality_score"] = quality_score
        
        # 提取覆盖率指标（如果存在）
        coverage_metrics = {}
        if "覆盖率" in result_content or "coverage" in result_content.lower():
            # 尝试提取具体的覆盖率数值
            import re
            coverage_patterns = [
                r"代码覆盖率[：:]\s*(\d+(?:\.\d+)?)%",
                r"功能覆盖率[：:]\s*(\d+(?:\.\d+)?)%",
                r"分支覆盖率[：:]\s*(\d+(?:\.\d+)?)%",
                r"语句覆盖率[：:]\s*(\d+(?:\.\d+)?)%",
                r"code coverage[：:]\s*(\d+(?:\.\d+)?)%",
                r"functional coverage[：:]\s*(\d+(?:\.\d+)?)%"
            ]
            
            for pattern in coverage_patterns:
                matches = re.findall(pattern, result_content, re.IGNORECASE)
                if matches:
                    coverage_metrics["coverage_percentage"] = float(matches[0])
                    break
        
        testing_workflow["test_coverage_metrics"] = coverage_metrics
        
        # 提取测试执行详情
        execution_details = {}
        if testing_workflow["simulation_executed"]:
            # 尝试提取仿真时间、周期等信息
            import re
            time_patterns = [
                r"仿真时间[：:]\s*(\d+(?:\.\d+)?)",
                r"simulation time[：:]\s*(\d+(?:\.\d+)?)",
                r"仿真周期[：:]\s*(\d+)",
                r"simulation cycles[：:]\s*(\d+)"
            ]
            
            for pattern in time_patterns:
                matches = re.findall(pattern, result_content, re.IGNORECASE)
                if matches:
                    if "时间" in pattern or "time" in pattern:
                        execution_details["simulation_time"] = float(matches[0])
                    else:
                        execution_details["simulation_cycles"] = int(matches[0])
                    break
        
        testing_workflow["test_execution_details"] = execution_details
        
        return testing_workflow
    
    def _identify_quality_issues(self, metrics: Dict[str, Any], file_verification: Dict[str, Any], 
                               execution_check: Dict[str, Any], testing_workflow: Dict[str, Any], original_request: str) -> List[str]:
        """识别质量问题"""
        issues = []
        
        # 文件生成问题
        if file_verification.get("missing_files"):
            issues.extend([f"缺失{file}" for file in file_verification["missing_files"]])
        
        # 执行问题
        if execution_check.get("missing_executions"):
            issues.extend(execution_check["missing_executions"])
        
        # 代码测试流程问题
        if testing_workflow.get("missing_testing_steps"):
            issues.extend([f"测试流程缺失: {step}" for step in testing_workflow["missing_testing_steps"]])
        
        if testing_workflow.get("workflow_completeness", 0) < 50 and ("测试" in original_request or "验证" in original_request):
            issues.append(f"测试流程完整性不足 ({testing_workflow['workflow_completeness']:.1f}%)")
        
        if testing_workflow.get("testing_quality_score", 0) < 50 and ("测试" in original_request or "验证" in original_request):
            issues.append(f"测试质量分数过低 ({testing_workflow['testing_quality_score']:.1f})")
        
        # 质量指标问题
        if metrics.get("test_coverage", 0) < 50 and ("测试" in original_request or "验证" in original_request):
            issues.append("测试覆盖率不足")
        
        if metrics.get("code_quality", 0) < 50:
            issues.append("代码质量需要提升")
        
        return issues
    
    def _identify_quality_strengths(self, metrics: Dict[str, Any], file_verification: Dict[str, Any], 
                                  execution_check: Dict[str, Any], testing_workflow: Dict[str, Any]) -> List[str]:
        """识别质量优势"""
        strengths = []
        
        if file_verification.get("all_required_files_generated"):
            strengths.append("所有必需文件已生成")
        
        if execution_check.get("simulation_actually_executed"):
            strengths.append("仿真验证已执行")
        
        # 代码测试流程优势
        if testing_workflow.get("workflow_completeness", 0) >= 80:
            strengths.append(f"测试流程完整性优秀 ({testing_workflow['workflow_completeness']:.1f}%)")
        
        if testing_workflow.get("testing_quality_score", 0) >= 80:
            strengths.append(f"测试质量分数优秀 ({testing_workflow['testing_quality_score']:.1f})")
        
        if testing_workflow.get("test_plan_created"):
            strengths.append("测试计划已创建")
        
        if testing_workflow.get("test_cases_designed"):
            strengths.append("测试用例已设计")
        
        if testing_workflow.get("testbench_generated"):
            strengths.append("测试台已生成")
        
        if testing_workflow.get("simulation_executed"):
            strengths.append("仿真已执行")
        
        if testing_workflow.get("test_results_analyzed"):
            strengths.append("测试结果已分析")
        
        if testing_workflow.get("coverage_analysis_performed"):
            strengths.append("覆盖率分析已完成")
        
        if testing_workflow.get("test_report_generated"):
            strengths.append("测试报告已生成")
        
        if metrics.get("code_quality", 0) >= 80:
            strengths.append("代码质量优秀")
        
        if metrics.get("documentation_quality", 0) >= 70:
            strengths.append("文档质量良好")
        
        return strengths
    
    def _generate_enhanced_recommendations(self, metrics: Dict[str, Any], quality_score: float, 
                                         quality_threshold: float, file_verification: Dict[str, Any],
                                         execution_check: Dict[str, Any], testing_workflow: Dict[str, Any], original_request: str) -> List[str]:
        """生成增强的改进建议"""
        recommendations = []
        
        # 基于文件验证的建议
        if not file_verification.get("all_required_files_generated"):
            if file_verification.get("missing_files"):
                recommendations.append(f"需要调用enhanced_real_code_review_agent生成缺失的文件: {', '.join(file_verification['missing_files'])}")
            else:
                recommendations.append("需要使用write_file工具实际生成文件，而非仅在报告中描述")
        
        # 基于执行检查的建议
        if not execution_check.get("simulation_actually_executed") and ("测试台" in original_request or "验证" in original_request):
            recommendations.append("需要调用enhanced_real_code_review_agent执行实际的仿真验证")
        
        # 基于代码测试流程的建议
        if testing_workflow.get("workflow_completeness", 0) < 50 and ("测试" in original_request or "验证" in original_request):
            missing_steps = testing_workflow.get("missing_testing_steps", [])
            if missing_steps:
                recommendations.append(f"需要完善测试流程，缺失步骤: {', '.join(missing_steps)}")
            else:
                recommendations.append("需要建立完整的代码测试流程")
        
        if not testing_workflow.get("test_plan_created") and ("测试" in original_request or "验证" in original_request):
            recommendations.append("需要创建详细的测试计划，包括测试目标、策略和范围")
        
        if not testing_workflow.get("test_cases_designed") and ("测试" in original_request or "验证" in original_request):
            recommendations.append("需要设计全面的测试用例，包括功能测试、边界测试和异常测试")
        
        if not testing_workflow.get("testbench_generated") and ("测试台" in original_request or "验证" in original_request):
            recommendations.append("需要生成完整的测试台文件，包含测试激励和结果验证")
        
        if not testing_workflow.get("simulation_executed") and ("仿真" in original_request or "验证" in original_request):
            recommendations.append("需要实际执行仿真验证，并提供仿真结果和波形分析")
        
        if not testing_workflow.get("test_results_analyzed") and ("测试" in original_request or "验证" in original_request):
            recommendations.append("需要对测试结果进行详细分析，验证功能正确性和时序正确性")
        
        if not testing_workflow.get("coverage_analysis_performed") and ("测试" in original_request or "验证" in original_request):
            recommendations.append("需要进行代码覆盖率分析，确保测试的完整性")
        
        if not testing_workflow.get("test_report_generated") and ("测试" in original_request or "验证" in original_request):
            recommendations.append("需要生成详细的测试报告，包含测试总结、结论和建议")
        
        # 基于测试质量分数的建议
        if testing_workflow.get("testing_quality_score", 0) < 50:
            recommendations.append("测试质量需要显著提升，建议重新设计测试策略")
        elif testing_workflow.get("testing_quality_score", 0) < 80:
            recommendations.append("测试质量良好，但仍有改进空间")
        
        # 基于质量分数的建议
        if quality_score < quality_threshold:
            if metrics.get("test_coverage", 0) < 50:
                recommendations.append("需要增强测试覆盖率，添加更多测试用例")
            if metrics.get("code_quality", 0) < 60:
                recommendations.append("需要改进代码质量，增加注释和优化结构")
        
        # 协作建议
        if len(recommendations) > 0:
            recommendations.append("建议启动多智能体协作模式以确保任务完整性")
        
        return recommendations
    
    def _analyze_detailed_metrics(self, content: str, result: Dict[str, Any], 
                                 file_verification: Dict[str, Any] = None, 
                                 execution_check: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析详细质量指标"""
        metrics = {
            "code_quality": 0.0,
            "documentation_quality": 0.0,
            "test_coverage": 0.0,
            "error_handling": 0.0,
            "performance": 0.0,
            "compliance": 0.0
        }
        
        content_lower = content.lower()
        
        # 代码质量评估
        if "module" in content_lower and "endmodule" in content_lower:
            metrics["code_quality"] += 30
        if "//" in content or "/*" in content:
            metrics["code_quality"] += 20
        if "parameter" in content_lower:
            metrics["code_quality"] += 10
        if "always" in content_lower or "assign" in content_lower:
            metrics["code_quality"] += 20
        
        # 文档质量评估
        if "module" in content_lower and "description" in content_lower:
            metrics["documentation_quality"] += 30
        if "//" in content and len(content.split("//")) > 5:
            metrics["documentation_quality"] += 20
        if "功能" in content or "function" in content_lower:
            metrics["documentation_quality"] += 20
        
        # 测试覆盖评估
        if "testbench" in content_lower or "test" in content_lower:
            metrics["test_coverage"] += 40
        if "simulation" in content_lower or "仿真" in content:
            metrics["test_coverage"] += 30
        if "verification" in content_lower or "验证" in content:
            metrics["test_coverage"] += 30
        
        # 错误处理评估
        if "error" in content_lower and "fix" in content_lower:
            metrics["error_handling"] += 40
        if "exception" in content_lower or "异常" in content:
            metrics["error_handling"] += 30
        if "check" in content_lower or "检查" in content:
            metrics["error_handling"] += 30
        
        # 性能评估
        execution_time = result.get("execution_time", 0)
        if execution_time > 0:
            if execution_time < 30:
                metrics["performance"] = 100
            elif execution_time < 60:
                metrics["performance"] = 80
            elif execution_time < 120:
                metrics["performance"] = 60
            else:
                metrics["performance"] = 40
        
        # 合规性评估
        if "verilog" in content_lower or "systemverilog" in content_lower:
            metrics["compliance"] += 50
        if "ieee" in content_lower or "标准" in content:
            metrics["compliance"] += 30
        if "synthesis" in content_lower or "综合" in content:
            metrics["compliance"] += 20
        
        return metrics
    
    def _calculate_comprehensive_quality_score(self, metrics: Dict[str, float], 
                                             file_verification: Dict[str, Any] = None,
                                             execution_check: Dict[str, Any] = None,
                                             testing_workflow: Dict[str, Any] = None) -> float:
        """计算综合质量分数 - 包含文件验证、实际执行和代码测试流程权重"""
        base_weights = {
            "code_quality": 0.20,
            "documentation_quality": 0.10,
            "test_coverage": 0.15,
            "error_handling": 0.10,
            "performance": 0.05,
            "compliance": 0.05
        }
        
        # 基础分数计算
        base_score = 0.0
        for metric, weight in base_weights.items():
            base_score += metrics.get(metric, 0.0) * weight
        
        # 文件验证权重 (15%)
        file_score = 0.0
        if file_verification:
            if file_verification.get("all_required_files_generated", False):
                file_score = 100.0
            elif file_verification.get("verilog_file_mentioned", False):
                file_score = 50.0  # 仅提到但未实际生成
            elif file_verification.get("files_actually_written", False):
                file_score = 30.0  # 有写入操作但不完整
        file_weighted_score = file_score * 0.15
        
        # 实际执行权重 (15%)
        execution_score = 0.0
        if execution_check:
            if execution_check.get("simulation_actually_executed", False):
                execution_score += 60.0
            elif execution_check.get("simulation_mentioned", False):
                execution_score += 20.0  # 仅提到但未实际执行
            
            if execution_check.get("tools_called", False):
                execution_score += 30.0
            
            if execution_check.get("concrete_results_provided", False):
                execution_score += 10.0
        execution_weighted_score = execution_score * 0.15
        
        # 代码测试流程权重 (20%)
        testing_workflow_score = 0.0
        if testing_workflow:
            workflow_completeness = testing_workflow.get("workflow_completeness", 0)
            testing_quality_score = testing_workflow.get("testing_quality_score", 0)
            
            # 基于工作流完整性的分数
            testing_workflow_score += workflow_completeness * 0.6  # 60%权重给完整性
            
            # 基于测试质量分数的分数
            testing_workflow_score += testing_quality_score * 0.4  # 40%权重给质量分数
            
            # 额外奖励：如果所有关键测试步骤都完成
            if (testing_workflow.get("test_plan_created") and 
                testing_workflow.get("test_cases_designed") and 
                testing_workflow.get("testbench_generated") and 
                testing_workflow.get("simulation_executed")):
                testing_workflow_score += 20.0  # 额外奖励
        testing_workflow_weighted_score = testing_workflow_score * 0.20
        
        # 综合分数
        total_score = base_score + file_weighted_score + execution_weighted_score + testing_workflow_weighted_score
        
        # 严格的惩罚机制：如果关键要求未满足，大幅降低分数
        if file_verification and not file_verification.get("all_required_files_generated", False):
            total_score *= 0.6  # 降低40%
        
        if execution_check and execution_check.get("missing_executions"):
            total_score *= 0.7  # 降低30%
        
        # 测试流程惩罚机制
        if testing_workflow and testing_workflow.get("workflow_completeness", 0) < 30:
            total_score *= 0.8  # 测试流程严重不完整，降低20%
        
        return min(100.0, max(0.0, total_score))
    
    def _generate_specific_recommendations(self, metrics: Dict[str, float], 
                                         quality_score: float, 
                                         threshold: float) -> List[str]:
        """生成具体改进建议"""
        recommendations = []
        
        if quality_score < threshold:
            if metrics["code_quality"] < 50:
                recommendations.append("提高代码质量：添加更多注释，改进代码结构")
            if metrics["documentation_quality"] < 40:
                recommendations.append("改进文档：添加详细的功能说明和使用示例")
            if metrics["test_coverage"] < 60:
                recommendations.append("增加测试覆盖：生成更全面的testbench")
            if metrics["error_handling"] < 30:
                recommendations.append("加强错误处理：添加边界条件检查和异常处理")
        
        if quality_score >= threshold:
            recommendations.append("质量达标，可以继续下一步或完成任务")
        
        return recommendations
    
    def _determine_enhanced_next_action(self, analysis: Dict[str, Any], 
                                      task_context: Dict[str, Any]) -> str:
        """确定增强的下一步行动 - 支持多智能体协作决策"""
        
        completeness = analysis.get("completeness", "unknown")
        quality_score = analysis.get("quality_score", 0)
        risk_assessment = analysis.get("risk_assessment", "low")
        file_verification = analysis.get("file_verification", {})
        execution_check = analysis.get("actual_execution_check", {})
        testing_workflow = analysis.get("code_testing_workflow", {})
        
        # 获取原始需求
        original_request = task_context.get("original_request", "") if task_context else ""
        
        # 先检查传统的完整性指标
        if completeness == "complete" and quality_score >= 80:
            # 即使报告完成，也要验证实际执行
            missing_files = file_verification.get("missing_files", [])
            missing_executions = execution_check.get("missing_executions", [])
            missing_testing_steps = testing_workflow.get("missing_testing_steps", [])
            
            if missing_files or missing_executions or missing_testing_steps:
                # 虽然智能体声称完成，但实际缺失关键项
                return "continue_iteration"  # 需要继续迭代
            else:
                return "complete_task"  # 真正完成
        
        elif completeness == "failed" or risk_assessment == "high":
            return "retry_with_different_agent"
        
        elif completeness == "partial" or quality_score < 70:
            # 检查是否需要多智能体协作
            missing_files = file_verification.get("missing_files", [])
            missing_executions = execution_check.get("missing_executions", [])
            missing_testing_steps = testing_workflow.get("missing_testing_steps", [])
            
            if (missing_files or missing_executions or missing_testing_steps or 
                not file_verification.get("all_required_files_generated", False) or
                testing_workflow.get("workflow_completeness", 0) < 50):
                return "continue_iteration"  # 需要额外的智能体协作
            else:
                return "improve_result"
        
        else:
            return "continue_iteration"
    
    def _generate_improvement_suggestions(self, analysis: Dict[str, Any], agent_id: str) -> List[str]:
        """生成改进建议 - 包含具体的智能体协作建议和工具调用指导"""
        suggestions = []
        
        # 获取验证结果
        file_verification = analysis.get("file_verification", {})
        execution_check = analysis.get("actual_execution_check", {})
        testing_workflow = analysis.get("code_testing_workflow", {})
        
        # 基于文件和执行验证生成具体建议
        missing_files = file_verification.get("missing_files", [])
        missing_executions = execution_check.get("missing_executions", [])
        missing_testing_steps = testing_workflow.get("missing_testing_steps", [])
        
        if missing_files or missing_executions or missing_testing_steps:
            suggestions.append("需要调用额外的智能体来补充缺失的功能")
            
            if "测试台文件" in missing_files or "仿真验证执行" in missing_executions:
                suggestions.append("建议调用 enhanced_real_code_review_agent 生成测试台并执行仿真")
                suggestions.append("  - 可用工具: generate_testbench, run_simulation, use_external_testbench")
                suggestions.append("  - 工具调用示例: generate_testbench(module_name='xxx', module_code='...')")
                suggestions.append("  - 工具调用示例: run_simulation(module_code='...', testbench_code='...')")
            
            if "Verilog模块文件" in missing_files:
                suggestions.append("建议重新调用 enhanced_real_verilog_agent 生成完整的Verilog模块")
                suggestions.append("  - 可用工具: analyze_design_requirements, generate_verilog_code, search_existing_modules")
                suggestions.append("  - 工具调用示例: analyze_design_requirements(requirements='...')")
                suggestions.append("  - 工具调用示例: generate_verilog_code(module_name='xxx', requirements='...')")
            
            # 基于测试流程缺失步骤的建议
            if missing_testing_steps:
                if "测试计划创建" in missing_testing_steps:
                    suggestions.append("需要创建详细的测试计划，包括测试目标、策略和范围")
                if "测试用例设计" in missing_testing_steps:
                    suggestions.append("需要设计全面的测试用例，包括功能测试、边界测试和异常测试")
                if "测试台生成" in missing_testing_steps:
                    suggestions.append("需要生成完整的测试台文件，包含测试激励和结果验证")
                    suggestions.append("  - 使用 enhanced_real_code_review_agent 的 generate_testbench 工具")
                if "仿真执行" in missing_testing_steps:
                    suggestions.append("需要实际执行仿真验证，并提供仿真结果和波形分析")
                    suggestions.append("  - 使用 enhanced_real_code_review_agent 的 run_simulation 工具")
                if "测试结果分析" in missing_testing_steps:
                    suggestions.append("需要对测试结果进行详细分析，验证功能正确性和时序正确性")
                    suggestions.append("  - 使用 enhanced_real_code_review_agent 的 analyze_test_failures 工具")
                if "覆盖率分析" in missing_testing_steps:
                    suggestions.append("需要进行代码覆盖率分析，确保测试的完整性")
                if "测试报告生成" in missing_testing_steps:
                    suggestions.append("需要生成详细的测试报告，包含测试总结、结论和建议")
        
        if not file_verification.get("all_required_files_generated", False):
            suggestions.append("需要确保所有文件都被实际生成而非仅在报告中描述")
        
        if not execution_check.get("simulation_actually_executed", False):
            suggestions.append("需要执行实际的仿真验证而非仅生成仿真代码")
        
        # 基于测试流程完整性的建议
        workflow_completeness = testing_workflow.get("workflow_completeness", 0)
        if workflow_completeness < 50:
            suggestions.append(f"测试流程完整性不足 ({workflow_completeness:.1f}%)，需要完善测试流程")
        elif workflow_completeness < 80:
            suggestions.append(f"测试流程基本完整 ({workflow_completeness:.1f}%)，但仍有改进空间")
        
        # 添加智能体工具调用指导
        suggestions.append("\n=== 智能体工具调用指导 ===")
        suggestions.append("LLMCoordinatorAgent 可用工具:")
        suggestions.append("  - assign_task_to_agent: 分配任务给指定智能体")
        suggestions.append("    调用示例: assign_task_to_agent(agent_id='enhanced_real_verilog_agent', task_description='...')")
        suggestions.append("  - analyze_agent_result: 分析智能体执行结果")
        suggestions.append("    调用示例: analyze_agent_result(agent_id='xxx', result={...}, quality_threshold=80)")
        suggestions.append("  - check_task_completion: 检查任务完成状态")
        suggestions.append("    调用示例: check_task_completion(task_id='xxx', all_results={...}, original_requirements='...')")
        suggestions.append("  - query_agent_status: 查询智能体状态")
        suggestions.append("    调用示例: query_agent_status(agent_id='enhanced_real_verilog_agent', include_performance=True)")
        suggestions.append("  - identify_task_type: 识别任务类型")
        suggestions.append("    调用示例: identify_task_type(user_request='...', context={...})")
        suggestions.append("  - recommend_agent: 推荐合适的智能体")
        suggestions.append("    调用示例: recommend_agent(task_type='design', task_description='...', priority='high')")
        suggestions.append("  - provide_final_answer: 提供最终答案")
        suggestions.append("    调用示例: provide_final_answer(final_summary='...', task_status='success')")
        
        suggestions.append("\nenhanced_real_verilog_agent 可用工具:")
        suggestions.append("  - analyze_design_requirements: 分析设计需求")
        suggestions.append("    调用示例: analyze_design_requirements(requirements='设计一个8位加法器', design_type='combinational')")
        suggestions.append("  - generate_verilog_code: 生成Verilog代码")
        suggestions.append("    调用示例: generate_verilog_code(module_name='adder_8bit', requirements='8位加法器', input_ports=[...])")
        suggestions.append("  - search_existing_modules: 搜索现有模块")
        suggestions.append("    调用示例: search_existing_modules(module_type='arithmetic', functionality='加法器')")
        suggestions.append("  - analyze_code_quality: 分析代码质量")
        suggestions.append("    调用示例: analyze_code_quality(verilog_code='...', module_name='adder_8bit')")
        suggestions.append("  - validate_design_specifications: 验证设计规格")
        suggestions.append("    调用示例: validate_design_specifications(requirements='...', generated_code='...')")
        suggestions.append("  - generate_design_documentation: 生成设计文档")
        suggestions.append("    调用示例: generate_design_documentation(module_name='adder_8bit', verilog_code='...', requirements='...')")
        suggestions.append("  - optimize_verilog_code: 优化Verilog代码")
        suggestions.append("    调用示例: optimize_verilog_code(verilog_code='...', optimization_target='area')")
        
        suggestions.append("\nenhanced_real_code_review_agent 可用工具:")
        suggestions.append("  - generate_testbench: 生成测试台")
        suggestions.append("    调用示例: generate_testbench(module_name='adder_8bit', module_code='...', test_scenarios=[...])")
        suggestions.append("  - run_simulation: 运行仿真")
        suggestions.append("    调用示例: run_simulation(module_code='...', testbench_code='...', simulator='iverilog')")
        suggestions.append("  - use_external_testbench: 使用外部测试台")
        suggestions.append("    调用示例: use_external_testbench(design_code='...', external_testbench_path='testbench.v', design_module_name='adder_8bit')")
        suggestions.append("  - generate_build_script: 生成构建脚本")
        suggestions.append("    调用示例: generate_build_script(verilog_files=['design.v'], testbench_files=['tb.v'], script_type='makefile')")
        suggestions.append("  - execute_build_script: 执行构建脚本")
        suggestions.append("    调用示例: execute_build_script(script_name='Makefile', action='all', timeout=300)")
        suggestions.append("  - analyze_test_failures: 分析测试失败")
        suggestions.append("    调用示例: analyze_test_failures(design_code='...', compilation_errors='...', testbench_code='...')")
        
        suggestions.append("\n=== 工具参数详细说明 ===")
        suggestions.append("LLMCoordinatorAgent 工具参数:")
        suggestions.append("  assign_task_to_agent:")
        suggestions.append("    - agent_id: 智能体ID ('enhanced_real_verilog_agent' 或 'enhanced_real_code_review_agent')")
        suggestions.append("    - task_description: 详细任务描述")
        suggestions.append("    - expected_output: 期望输出格式")
        suggestions.append("    - task_type: 任务类型 ('design', 'verification', 'analysis', 'debug', 'composite')")
        suggestions.append("    - priority: 优先级 ('high', 'medium', 'low')")
        
        suggestions.append("  analyze_agent_result:")
        suggestions.append("    - agent_id: 智能体ID")
        suggestions.append("    - result: 智能体执行结果")
        suggestions.append("    - task_context: 任务上下文")
        suggestions.append("    - quality_threshold: 质量阈值 (0-100)")
        
        suggestions.append("\nenhanced_real_verilog_agent 工具参数:")
        suggestions.append("  generate_verilog_code:")
        suggestions.append("    - module_name: 模块名称 (字母开头)")
        suggestions.append("    - requirements: 设计需求描述")
        suggestions.append("    - input_ports: 输入端口列表 [{'name': 'clk', 'width': 1}]")
        suggestions.append("    - output_ports: 输出端口列表 [{'name': 'result', 'width': 8}]")
        suggestions.append("    - coding_style: 编码风格 ('behavioral', 'structural', 'rtl', 'mixed')")
        
        suggestions.append("  analyze_design_requirements:")
        suggestions.append("    - requirements: 设计需求描述")
        suggestions.append("    - design_type: 设计类型 ('combinational', 'sequential', 'mixed', 'custom')")
        suggestions.append("    - complexity_level: 复杂度 ('simple', 'medium', 'complex', 'advanced')")
        
        suggestions.append("\nenhanced_real_code_review_agent 工具参数:")
        suggestions.append("  generate_testbench:")
        suggestions.append("    - module_name: 目标模块名称")
        suggestions.append("    - module_code: 完整的Verilog模块代码")
        suggestions.append("    - test_scenarios: 测试场景列表")
        suggestions.append("    - clock_period: 时钟周期 (ns)")
        suggestions.append("    - simulation_time: 仿真时间 (时钟周期数)")
        
        suggestions.append("  run_simulation:")
        suggestions.append("    - module_code: 模块代码内容")
        suggestions.append("    - testbench_code: 测试台代码内容")
        suggestions.append("    - simulator: 仿真器 ('iverilog', 'modelsim', 'vivado', 'auto')")
        suggestions.append("    - simulation_options: 仿真选项")
        
        suggestions.append("  analyze_test_failures:")
        suggestions.append("    - design_code: 设计代码")
        suggestions.append("    - compilation_errors: 编译错误信息")
        suggestions.append("    - simulation_errors: 仿真错误信息")
        suggestions.append("    - test_assertions: 测试断言失败信息")
        suggestions.append("    - testbench_code: 测试台代码")
        suggestions.append("    - iteration_number: 当前迭代次数")
        
        suggestions.append("\n=== 工具调用最佳实践 ===")
        suggestions.append("1. 任务分配流程:")
        suggestions.append("   - 先使用 identify_task_type 识别任务类型")
        suggestions.append("   - 使用 recommend_agent 推荐合适的智能体")
        suggestions.append("   - 使用 assign_task_to_agent 分配任务")
        suggestions.append("   - 使用 analyze_agent_result 分析结果")
        suggestions.append("   - 使用 check_task_completion 检查完成状态")
        
        suggestions.append("2. Verilog设计流程:")
        suggestions.append("   - 使用 analyze_design_requirements 分析需求")
        suggestions.append("   - 使用 search_existing_modules 搜索现有模块")
        suggestions.append("   - 使用 generate_verilog_code 生成代码")
        suggestions.append("   - 使用 analyze_code_quality 分析质量")
        suggestions.append("   - 使用 validate_design_specifications 验证规格")
        
        suggestions.append("3. 测试验证流程:")
        suggestions.append("   - 使用 generate_testbench 生成测试台")
        suggestions.append("   - 使用 run_simulation 执行仿真")
        suggestions.append("   - 使用 analyze_test_failures 分析失败")
        suggestions.append("   - 使用 generate_build_script 生成构建脚本")
        suggestions.append("   - 使用 execute_build_script 执行构建")
        
        suggestions.append("4. 错误处理策略:")
        suggestions.append("   - 编译错误: 检查语法和端口定义")
        suggestions.append("   - 仿真错误: 检查时序和逻辑")
        suggestions.append("   - 测试失败: 分析断言和期望值")
        suggestions.append("   - 质量不足: 重新设计或优化代码")
        
        # 添加LLMCoordinatorAgent的工具使用指导
        coordinator_guide = self._generate_coordinator_tool_guide()
        suggestions.extend(coordinator_guide)
        
        # 基于测试质量分数的建议
        testing_quality_score = testing_workflow.get("testing_quality_score", 0)
        if testing_quality_score < 50:
            suggestions.append(f"测试质量分数过低 ({testing_quality_score:.1f})，需要重新设计测试策略")
        elif testing_quality_score < 80:
            suggestions.append(f"测试质量良好 ({testing_quality_score:.1f})，但仍有改进空间")
        
        # 基于质量分数生成建议
        if analysis.get("quality_score", 0) < 70:
            suggestions.append("质量分数偏低，需要改进或使用多智能体协作")
        
        # 基于智能体历史表现生成建议
        if agent_id in self.registered_agents:
            agent_info = self.registered_agents[agent_id]
            if agent_info.consecutive_failures > 2:
                suggestions.append("该智能体连续失败次数较多，建议更换智能体")
        
        return suggestions
    
    def _generate_coordinator_tool_guide(self) -> List[str]:
        """生成LLMCoordinatorAgent专用的工具使用指导"""
        guide = []
        
        guide.append("\n=== LLMCoordinatorAgent 工具调用指导 ===")
        guide.append("")
        
        guide.append("【可用工具列表】")
        guide.append("1. assign_task_to_agent - 智能任务分配")
        guide.append("   功能: 将任务分配给最合适的智能体")
        guide.append("   参数: agent_id, task_description, expected_output, task_type, priority")
        guide.append("   示例: assign_task_to_agent('enhanced_real_verilog_agent', '设计8位加法器', '', 'design', 'high')")
        guide.append("")
        
        guide.append("2. analyze_agent_result - 结果质量分析")
        guide.append("   功能: 深度分析智能体执行结果的质量和完整性")
        guide.append("   参数: agent_id, result, task_context, quality_threshold")
        guide.append("   示例: analyze_agent_result('verilog_agent', result_data, context, 80.0)")
        guide.append("")
        
        guide.append("3. check_task_completion - 任务完成检查")
        guide.append("   功能: 检查任务是否真正完成，评估整体质量")
        guide.append("   参数: task_id, all_results, original_requirements, completion_criteria")
        guide.append("   示例: check_task_completion('task_001', results, '设计8位加法器')")
        guide.append("")
        
        guide.append("4. query_agent_status - 智能体状态查询")
        guide.append("   功能: 查询智能体的详细状态和性能指标")
        guide.append("   参数: agent_id, include_performance, include_history")
        guide.append("   示例: query_agent_status('enhanced_real_verilog_agent', True, False)")
        guide.append("")
        
        guide.append("5. identify_task_type - 任务类型识别")
        guide.append("   功能: 智能识别任务类型，支持设计、验证、分析等")
        guide.append("   参数: user_request, context")
        guide.append("   示例: identify_task_type('设计一个计数器', {})")
        guide.append("")
        
        guide.append("6. recommend_agent - 智能体推荐")
        guide.append("   功能: 基于任务特征推荐最合适的智能体")
        guide.append("   参数: task_type, task_description, priority, constraints")
        guide.append("   示例: recommend_agent('design', '设计ALU', 'high')")
        guide.append("")
        
        guide.append("7. provide_final_answer - 最终答案提供")
        guide.append("   功能: 当任务完成时提供最终的完整答案")
        guide.append("   参数: final_summary, task_status, results_summary")
        guide.append("   示例: provide_final_answer('任务完成', 'success', results)")
        guide.append("")
        
        guide.append("8. get_tool_usage_guide - 工具使用指导")
        guide.append("   功能: 获取完整的工具使用指导")
        guide.append("   参数: agent_type, include_examples, include_best_practices")
        guide.append("   示例: get_tool_usage_guide('coordinator', True, True)")
        guide.append("")
        
        guide.append("【🎯 强制执行的协调流程】")
        guide.append("1. **第一步**: identify_task_type → 识别任务类型")
        guide.append("2. **第二步**: recommend_agent → 推荐最合适的智能体")
        guide.append("3. **第三步**: assign_task_to_agent → 分配任务给推荐智能体")
        guide.append("4. **第四步**: analyze_agent_result → 分析执行结果")
        guide.append("5. **第五步**: 根据分析结果决定是否需要继续迭代")
        guide.append("")
        
        guide.append("【⚠️ 重要规则】")
        guide.append("- **必须严格按照上述流程执行，不得跳过任何步骤**")
        guide.append("- **推荐代理工具 recommend_agent 是必需的，不能直接调用 assign_task_to_agent**")
        guide.append("- **每次任务分配前都必须先调用推荐代理工具**")
        guide.append("- **分析结果后再决定下一步行动**")
        guide.append("- **确保任务完成后再提供最终答案**")
        guide.append("")
        
        guide.append("【❌ 错误示例（禁止）】")
        guide.append("- 直接调用 assign_task_to_agent 而不先调用 recommend_agent")
        guide.append("- 跳过 identify_task_type 直接推荐智能体")
        guide.append("- 不分析结果就继续分配任务")
        guide.append("")
        
        guide.append("【✅ 正确示例】")
        guide.append("- identify_task_type → recommend_agent → assign_task_to_agent")
        guide.append("- 每次分配任务前都先推荐智能体")
        guide.append("- 分析结果后再决定下一步")
        guide.append("")
        
        guide.append("【注意事项】")
        guide.append("- 作为协调者，主要负责任务分配和结果分析")
        guide.append("- 具体的设计和验证工作交给专门的智能体")
        guide.append("- 确保任务描述清晰，便于其他智能体理解执行")
        guide.append("- 定期检查任务执行状态和质量")
        
        return guide
    
    async def _tool_check_task_completion(self, task_id: str, 
                                        all_results: Dict[str, Any],
                                        original_requirements: str,
                                        completion_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """增强的任务完成检查"""
        
        try:
            # 检查任务是否存在
            if task_id not in self.active_tasks:
                return {
                    "success": False,
                    "error": f"任务不存在: {task_id}"
                }
            
            task_context = self.active_tasks[task_id]
            
            # 分析所有结果
            completion_analysis = self._enhanced_task_completion_analysis(
                all_results, original_requirements, task_context, completion_criteria
            )
            
            # 更新任务状态
            if completion_analysis["is_completed"]:
                task_context.completion_status = "completed"
                task_context.quality_score = completion_analysis["completion_score"]
                self._update_performance_metrics(task_context, True)
            else:
                task_context.completion_status = "in_progress"
                task_context.quality_score = completion_analysis["completion_score"]
            
            return {
                "success": True,
                "is_completed": completion_analysis["is_completed"],
                "completion_score": completion_analysis["completion_score"],
                "missing_requirements": completion_analysis["missing_requirements"],
                "quality_assessment": completion_analysis["quality_assessment"],
                "detailed_analysis": completion_analysis["detailed_analysis"],
                "next_steps": completion_analysis["next_steps"],
                "performance_metrics": completion_analysis["performance_metrics"]
            }
            
        except Exception as e:
            self.logger.error(f"❌ 任务完成检查失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _enhanced_task_completion_analysis(self, all_results: Dict[str, Any],
                                         original_requirements: str,
                                         task_context: TaskContext,
                                         completion_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """增强的任务完成情况分析"""
        
        analysis = {
            "is_completed": False,
            "completion_score": 0.0,
            "missing_requirements": [],
            "quality_assessment": "unknown",
            "detailed_analysis": {},
            "next_steps": [],
            "performance_metrics": {}
        }
        
        # 检查是否有结果
        if not all_results:
            analysis["missing_requirements"].append("没有执行结果")
            analysis["next_steps"].append("开始任务执行")
            return analysis
        
        # 分析原始需求
        requirements = original_requirements.lower()
        
        # 详细分析各项指标
        detailed_analysis = self._analyze_completion_metrics(all_results, requirements, task_context)
        analysis["detailed_analysis"] = detailed_analysis
        
        # 计算完成分数
        completion_score = self._calculate_completion_score(detailed_analysis, completion_criteria)
        analysis["completion_score"] = completion_score
        
        # 检查缺失项
        missing_items = self._identify_missing_requirements(detailed_analysis, requirements)
        analysis["missing_requirements"] = missing_items
        
        # 判断是否完成
        is_completed = self._determine_completion_status(completion_score, missing_items, completion_criteria)
        analysis["is_completed"] = is_completed
        
        # 质量评估
        analysis["quality_assessment"] = self._assess_overall_quality(detailed_analysis, completion_score)
        
        # 确定下一步行动
        analysis["next_steps"] = self._determine_next_steps(is_completed, missing_items, detailed_analysis)
        
        # 性能指标
        analysis["performance_metrics"] = self._calculate_performance_metrics(task_context, all_results)
        
        return analysis
    
    def _analyze_completion_metrics(self, all_results: Dict[str, Any], 
                                  requirements: str,
                                  task_context: TaskContext) -> Dict[str, Any]:
        """分析完成指标"""
        metrics = {
            "design_complete": False,
            "verification_complete": False,
            "documentation_complete": False,
            "testing_complete": False,
            "quality_checks_passed": False,
            "agent_performance": {},
            "execution_time": 0.0,
            "total_iterations": 0
        }
        
        # 🎯 修复：处理all_results可能是列表的情况
        if isinstance(all_results, list):
            # 如果是列表，转换为字典格式
            results_dict = {}
            for i, result in enumerate(all_results):
                if isinstance(result, dict):
                    # 尝试从结果中提取智能体ID
                    agent_id = result.get("agent_id", f"agent_{i}")
                    results_dict[agent_id] = result
                else:
                    results_dict[f"result_{i}"] = result
            all_results = results_dict
            self.logger.info(f"🎯 将列表格式的all_results转换为字典格式，包含{len(all_results)}个结果")
        
        # 检查设计完成情况
        if "design" in requirements or "模块" in requirements:
            design_results = []
            for agent_id, result in all_results.items():
                if agent_id == "enhanced_real_verilog_agent":
                    design_results.append(result)
            
            if design_results:
                metrics["design_complete"] = any(
                    "module" in str(result).lower() and "endmodule" in str(result).lower()
                    for result in design_results
                )
        
        # 检查验证完成情况
        if "test" in requirements or "验证" in requirements or "testbench" in requirements:
            verification_results = []
            for agent_id, result in all_results.items():
                if agent_id == "enhanced_real_code_review_agent":
                    verification_results.append(result)
            
            if verification_results:
                metrics["verification_complete"] = any(
                    "testbench" in str(result).lower() or "simulation" in str(result).lower()
                    for result in verification_results
                )
        
        # 检查文档完成情况
        doc_results = []
        for result in all_results.values():
            if "documentation" in str(result).lower() or "文档" in str(result):
                doc_results.append(result)
        
        metrics["documentation_complete"] = len(doc_results) > 0
        
        # 检查测试完成情况
        test_results = []
        for result in all_results.values():
            if "test" in str(result).lower() or "仿真" in str(result):
                test_results.append(result)
        
        metrics["testing_complete"] = len(test_results) > 0
        
        # 检查质量检查
        quality_results = []
        for result in all_results.values():
            if "quality" in str(result).lower() or "质量" in str(result):
                quality_results.append(result)
        
        metrics["quality_checks_passed"] = len(quality_results) > 0
        
        # 智能体性能分析
        for agent_id, result in all_results.items():
            if isinstance(result, dict):
                execution_time = result.get("execution_time", 0)
                metrics["agent_performance"][agent_id] = {
                    "execution_time": execution_time,
                    "success": result.get("success", False),
                    "quality_score": result.get("quality_score", 0)
                }
                metrics["execution_time"] += execution_time
        
        metrics["total_iterations"] = task_context.iteration_count
        
        return metrics
    
    def _calculate_completion_score(self, detailed_analysis: Dict[str, Any],
                                  completion_criteria: Dict[str, Any] = None) -> float:
        """计算完成分数"""
        score = 0.0
        
        # 基础完成指标权重
        weights = {
            "design_complete": 0.35,
            "verification_complete": 0.30,
            "documentation_complete": 0.15,
            "testing_complete": 0.15,
            "quality_checks_passed": 0.05
        }
        
        # 应用权重
        for metric, weight in weights.items():
            if detailed_analysis.get(metric, False):
                score += weight * 100
        
        # 考虑智能体性能
        agent_performance = detailed_analysis.get("agent_performance", {})
        if agent_performance:
            avg_quality = sum(
                perf.get("quality_score", 0) for perf in agent_performance.values()
            ) / len(agent_performance)
            score += avg_quality * 0.1  # 10%权重给质量分数
        
        return min(100.0, score)
    
    def _identify_missing_requirements(self, detailed_analysis: Dict[str, Any],
                                     requirements: str) -> List[str]:
        """识别缺失的需求"""
        missing = []
        
        # 检查设计需求
        if ("design" in requirements or "模块" in requirements) and not detailed_analysis.get("design_complete", False):
            missing.append("缺少Verilog模块设计")
        
        # 检查验证需求
        if ("test" in requirements or "验证" in requirements or "testbench" in requirements) and not detailed_analysis.get("verification_complete", False):
            missing.append("缺少测试台和验证")
        
        # 检查文档需求
        if not detailed_analysis.get("documentation_complete", False):
            missing.append("缺少设计文档")
        
        # 检查测试需求
        if not detailed_analysis.get("testing_complete", False):
            missing.append("缺少测试执行")
        
        # 检查质量需求
        if not detailed_analysis.get("quality_checks_passed", False):
            missing.append("缺少质量检查")
        
        return missing
    
    def _determine_completion_status(self, completion_score: float,
                                   missing_requirements: List[str],
                                   completion_criteria: Dict[str, Any] = None) -> bool:
        """确定完成状态"""
        
        # 使用自定义完成标准
        if completion_criteria:
            required_score = completion_criteria.get("required_score", 80.0)
            max_missing_items = completion_criteria.get("max_missing_items", 0)
            
            return (completion_score >= required_score and 
                   len(missing_requirements) <= max_missing_items)
        
        # 默认完成标准
        return completion_score >= 80.0 and len(missing_requirements) == 0
    
    def _assess_overall_quality(self, detailed_analysis: Dict[str, Any],
                              completion_score: float) -> str:
        """评估整体质量"""
        if completion_score >= 90:
            return "excellent"
        elif completion_score >= 80:
            return "good"
        elif completion_score >= 70:
            return "fair"
        elif completion_score >= 60:
            return "poor"
        else:
            return "very_poor"
    
    def _determine_next_steps(self, is_completed: bool,
                            missing_requirements: List[str],
                            detailed_analysis: Dict[str, Any]) -> List[str]:
        """确定下一步行动"""
        next_steps = []
        
        if is_completed:
            next_steps.append("任务完成，可以交付结果")
        else:
            # 根据缺失项确定下一步
            if "缺少Verilog模块设计" in missing_requirements:
                next_steps.append("分配设计任务给enhanced_real_verilog_agent")
            
            if "缺少测试台和验证" in missing_requirements:
                next_steps.append("分配验证任务给enhanced_real_code_review_agent")
            
            if "缺少设计文档" in missing_requirements:
                next_steps.append("要求智能体生成设计文档")
            
            if "缺少测试执行" in missing_requirements:
                next_steps.append("执行测试验证")
            
            if "缺少质量检查" in missing_requirements:
                next_steps.append("进行代码质量检查")
        
        return next_steps
    
    def _calculate_performance_metrics(self, task_context: TaskContext,
                                     all_results: Dict[str, Any]) -> Dict[str, Any]:
        """计算性能指标"""
        metrics = {
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "success_rate": 0.0,
            "agent_utilization": {},
            "iteration_efficiency": 0.0
        }
        
        # 🎯 修复：处理all_results可能是列表的情况
        if isinstance(all_results, list):
            # 如果是列表，转换为字典格式
            results_dict = {}
            for i, result in enumerate(all_results):
                if isinstance(result, dict):
                    agent_id = result.get("agent_id", f"agent_{i}")
                    results_dict[agent_id] = result
                else:
                    results_dict[f"result_{i}"] = result
            all_results = results_dict
            self.logger.info(f"🎯 性能指标计算中将列表格式的all_results转换为字典格式，包含{len(all_results)}个结果")
        
        # 计算总执行时间
        total_time = 0.0
        success_count = 0
        total_count = len(all_results)
        
        for result in all_results.values():
            if isinstance(result, dict):
                execution_time = result.get("execution_time", 0)
                total_time += execution_time
                
                if result.get("success", False):
                    success_count += 1
        
        metrics["total_execution_time"] = total_time
        metrics["average_execution_time"] = total_time / total_count if total_count > 0 else 0
        metrics["success_rate"] = success_count / total_count if total_count > 0 else 0
        
        # 计算迭代效率
        if task_context.iteration_count > 0:
            # 🎯 修复：使用task_context中的quality_score而不是未定义的completion_score
            metrics["iteration_efficiency"] = task_context.quality_score / task_context.iteration_count
        
        # 智能体利用率
        for agent_id, agent_info in self.registered_agents.items():
            if agent_id in all_results:
                metrics["agent_utilization"][agent_id] = {
                    "tasks_assigned": 1,
                    "success_rate": 1.0 if all_results[agent_id].get("success", False) else 0.0,
                    "average_time": all_results[agent_id].get("execution_time", 0)
                }
        
        return metrics
    
    def _update_performance_metrics(self, task_context: TaskContext, success: bool):
        """更新性能指标"""
        self.performance_metrics["total_tasks"] += 1
        
        if success:
            self.performance_metrics["successful_tasks"] += 1
        else:
            self.performance_metrics["failed_tasks"] += 1
        
        # 更新平均完成时间
        execution_time = time.time() - task_context.start_time
        total_tasks = self.performance_metrics["total_tasks"]
        current_avg = self.performance_metrics["average_completion_time"]
        
        self.performance_metrics["average_completion_time"] = (
            (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        )
    
    async def _tool_query_agent_status(self, agent_id: str,
                                     include_performance: bool = True,
                                     include_history: bool = False) -> Dict[str, Any]:
        """增强的智能体状态查询"""
        
        try:
            if agent_id not in self.registered_agents:
                return {
                    "success": False,
                    "error": f"智能体不存在: {agent_id}"
                }
            
            agent_info = self.registered_agents[agent_id]
            
            # 基础状态信息
            status_info = {
                "success": True,
                "agent_id": agent_id,
                "status": agent_info.status.value,
                "capabilities": [cap.value for cap in agent_info.capabilities],
                "specialty": agent_info.specialty,
                "conversation_id": agent_info.conversation_id,
                "last_used": agent_info.last_used
            }
            
            # 性能指标
            if include_performance:
                performance_metrics = self._calculate_agent_performance_metrics(agent_info)
                status_info["performance_metrics"] = performance_metrics
            
            # 历史记录
            if include_history:
                history_data = self._get_agent_history(agent_id)
                status_info["history"] = history_data
            
            # 健康状态评估
            health_assessment = self._assess_agent_health(agent_info)
            status_info["health_assessment"] = health_assessment
            
            # 推荐任务类型
            recommended_tasks = self._get_recommended_task_types(agent_info)
            status_info["recommended_tasks"] = recommended_tasks
            
            return status_info
            
        except Exception as e:
            self.logger.error(f"❌ 查询智能体状态失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_agent_performance_metrics(self, agent_info: AgentInfo) -> Dict[str, Any]:
        """计算智能体性能指标"""
        total_tasks = agent_info.success_count + agent_info.failure_count
        
        metrics = {
            "total_tasks": total_tasks,
            "success_count": agent_info.success_count,
            "failure_count": agent_info.failure_count,
            "success_rate": agent_info.success_count / total_tasks if total_tasks > 0 else 0.0,
            "average_response_time": agent_info.average_response_time,
            "total_execution_time": agent_info.total_execution_time,
            "consecutive_successes": agent_info.consecutive_successes,
            "consecutive_failures": agent_info.consecutive_failures,
            "last_success_time": agent_info.last_success_time,
            "last_failure_time": agent_info.last_failure_time
        }
        
        # 计算趋势指标
        if agent_info.last_success_time and agent_info.last_failure_time:
            if agent_info.last_success_time > agent_info.last_failure_time:
                metrics["recent_trend"] = "improving"
            else:
                metrics["recent_trend"] = "declining"
        elif agent_info.last_success_time:
            metrics["recent_trend"] = "stable_success"
        elif agent_info.last_failure_time:
            metrics["recent_trend"] = "stable_failure"
        else:
            metrics["recent_trend"] = "unknown"
        
        # 计算可靠性评分
        reliability_score = self._calculate_reliability_score(agent_info)
        metrics["reliability_score"] = reliability_score
        
        return metrics
    
    def _calculate_reliability_score(self, agent_info: AgentInfo) -> float:
        """计算可靠性评分"""
        total_tasks = agent_info.success_count + agent_info.failure_count
        if total_tasks == 0:
            return 0.0
        
        # 基础成功率
        base_score = agent_info.success_count / total_tasks * 100
        
        # 连续成功奖励
        consecutive_bonus = min(10.0, agent_info.consecutive_successes * 2.0)
        
        # 响应时间奖励
        time_bonus = 0.0
        if agent_info.average_response_time > 0:
            if agent_info.average_response_time < 30:
                time_bonus = 10.0
            elif agent_info.average_response_time < 60:
                time_bonus = 5.0
        
        # 连续失败惩罚
        consecutive_penalty = min(20.0, agent_info.consecutive_failures * 5.0)
        
        final_score = base_score + consecutive_bonus + time_bonus - consecutive_penalty
        return max(0.0, min(100.0, final_score))
    
    def _get_agent_history(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体历史记录"""
        # 这里可以从数据库或日志中获取更详细的历史记录
        # 目前返回基本的历史统计
        return {
            "total_executions": 0,
            "recent_performance": [],
            "common_issues": [],
            "improvement_trend": "stable"
        }
    
    def _assess_agent_health(self, agent_info: AgentInfo) -> Dict[str, Any]:
        """评估智能体健康状态"""
        health = {
            "status": "healthy",
            "score": 100.0,
            "issues": [],
            "recommendations": []
        }
        
        # 检查连续失败
        if agent_info.consecutive_failures > 3:
            health["status"] = "warning"
            health["score"] -= 30
            health["issues"].append(f"连续失败{agent_info.consecutive_failures}次")
            health["recommendations"].append("建议检查智能体配置或更换智能体")
        
        # 检查成功率
        total_tasks = agent_info.success_count + agent_info.failure_count
        if total_tasks > 0:
            success_rate = agent_info.success_count / total_tasks
            if success_rate < 0.5:
                health["status"] = "critical"
                health["score"] -= 50
                health["issues"].append(f"成功率过低: {success_rate:.1%}")
                health["recommendations"].append("建议重新配置或更换智能体")
            elif success_rate < 0.7:
                health["status"] = "warning"
                health["score"] -= 20
                health["issues"].append(f"成功率偏低: {success_rate:.1%}")
                health["recommendations"].append("建议优化智能体配置")
        
        # 检查响应时间
        if agent_info.average_response_time > 120:
            health["status"] = "warning"
            health["score"] -= 15
            health["issues"].append(f"响应时间过长: {agent_info.average_response_time:.1f}秒")
            health["recommendations"].append("建议优化性能或检查网络连接")
        
        # 检查长期未使用
        if agent_info.last_used:
            time_since_last_use = time.time() - agent_info.last_used
            if time_since_last_use > 3600:  # 1小时
                health["issues"].append(f"长期未使用: {time_since_last_use/3600:.1f}小时")
        
        health["score"] = max(0.0, health["score"])
        
        return health
    
    def _get_recommended_task_types(self, agent_info: AgentInfo) -> List[str]:
        """获取推荐的任务类型"""
        recommended = []
        
        # 基于智能体ID推荐
        if agent_info.agent_id == "enhanced_real_verilog_agent":
            recommended.extend(["design", "code_generation", "module_implementation"])
        elif agent_info.agent_id == "enhanced_real_code_review_agent":
            recommended.extend(["verification", "analysis", "debug", "testbench_generation"])
        
        # 基于历史表现推荐
        if agent_info.consecutive_successes > 2:
            recommended.append("high_priority_tasks")
        
        if agent_info.average_response_time < 30:
            recommended.append("time_sensitive_tasks")
        
        return list(set(recommended))  # 去重
    
    async def _collect_agent_conversations(self, task_context: TaskContext):
        """收集已分配智能体的对话历史到任务上下文"""
        try:
            for agent_id, agent_result in task_context.agent_results.items():
                # 获取智能体实例
                agent_instance = None
                
                # 从注册的智能体中查找
                for registered_agent_id, registered_agent in self.registered_agents.items():
                    if registered_agent_id == agent_id or registered_agent.agent_id == agent_id:
                        agent_instance = registered_agent
                        break
                
                if agent_instance and hasattr(agent_instance, 'conversation_history'):
                    self.logger.info(f"📥 收集智能体 {agent_id} 的对话历史: {len(agent_instance.conversation_history)} 条消息")
                    
                    # 将智能体的对话历史合并到任务上下文
                    for msg in agent_instance.conversation_history:
                        # 避免重复添加相同的消息
                        msg_signature = f"{msg.get('role', '')}_{msg.get('agent_id', '')}_{hash(msg.get('content', ''))}"
                        existing_signatures = [
                            f"{existing_msg.get('role', '')}_{existing_msg.get('agent_id', '')}_{hash(existing_msg.get('content', ''))}"
                            for existing_msg in task_context.conversation_history
                        ]
                        
                        if msg_signature not in existing_signatures:
                            # 标记消息来源并添加到任务上下文
                            msg_copy = msg.copy()
                            msg_copy['source_agent'] = agent_id
                            msg_copy['collected_timestamp'] = time.time()
                            task_context.conversation_history.append(msg_copy)
                else:
                    self.logger.warning(f"⚠️ 无法找到智能体 {agent_id} 的实例或对话历史")
                    
        except Exception as e:
            self.logger.error(f"❌ 收集智能体对话历史失败: {str(e)}")
    
    def _collect_final_result(self, task_context: TaskContext, 
                            coordination_result: str) -> Dict[str, Any]:
        """收集最终结果"""
        
        # 🆕 计算性能指标
        total_execution_time = time.time() - task_context.start_time
        performance_metrics = {
            "total_execution_time": total_execution_time,
            "average_tool_execution_time": sum(t.get("execution_time", 0) or 0 for t in task_context.tool_executions) / max(len(task_context.tool_executions), 1),
            "total_file_operations": len(task_context.file_operations),
            "total_workflow_stages": len(task_context.workflow_stages),
            "success_rate": len([t for t in task_context.tool_executions if t.get("success", True)]) / max(len(task_context.tool_executions), 1)
        }
        
        # 更新TaskContext的性能指标
        task_context.update_performance_metrics(performance_metrics)
        
        return {
            "success": True,
            "task_id": task_context.task_id,
            "coordination_result": coordination_result,
            "agent_results": task_context.agent_results,
            "execution_summary": {
                "total_iterations": task_context.iteration_count,
                "assigned_agents": list(task_context.agent_results.keys()),
                "execution_time": total_execution_time
            },
            "conversation_history": task_context.conversation_history,
            # 🆕 包含完整的TaskContext数据用于Gradio可视化
            "task_context": {
                "tool_executions": task_context.tool_executions,
                "agent_interactions": task_context.agent_interactions,
                "performance_metrics": task_context.performance_metrics,
                "workflow_stages": task_context.workflow_stages,
                "file_operations": task_context.file_operations,
                "execution_timeline": task_context.execution_timeline,
                "llm_conversations": task_context.llm_conversations,
                "data_collection_summary": task_context.get_data_collection_summary()
            }
        }
    
    def get_registered_agents(self) -> Dict[str, AgentInfo]:
        """获取已注册的智能体"""
        return self.registered_agents
    
    def get_registered_tools(self) -> List[Dict[str, Any]]:
        """获取已注册的工具"""
        return self.enhanced_tools if hasattr(self, 'enhanced_tools') else [].copy()
    
    def get_active_tasks(self) -> Dict[str, TaskContext]:
        """获取活跃任务"""
        return self.active_tasks.copy()
    
    async def _run_coordination_loop(self, task_context: TaskContext, initial_result: str, 
                                   conversation_id: str, max_iterations: int) -> Dict[str, Any]:
        """运行持续协调循环，监听智能体结果并继续协调"""
        self.logger.info(f"🔄 开始持续协调循环 - 任务ID: {task_context.task_id}")
        self.logger.info(f"🔍 当前智能体结果数量: {len(task_context.agent_results)}")
        self.logger.info(f"🔍 智能体结果键: {list(task_context.agent_results.keys())}")
        
        # 🔍 新增：检查是否有智能体结果，如果没有则强制分配任务
        if not task_context.agent_results:
            self.logger.warning("⚠️ 没有智能体结果，检查是否需要强制分配任务")
            
            # 检查对话历史中是否有assign_task_to_agent调用
            assign_task_found = False
            for msg in task_context.conversation_history:
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    if "assign_task_to_agent" in content:
                        assign_task_found = True
                        break
            
            if not assign_task_found:
                self.logger.warning("⚠️ 对话历史中没有找到assign_task_to_agent调用，强制分配任务")
                forced_result = await self._force_assign_task(task_context.original_request, task_context)
                if forced_result.get("success", False):
                    self.logger.info("✅ 强制分配任务成功，继续协调循环")
                else:
                    self.logger.error("❌ 强制分配任务失败")
                    return {
                        "success": False,
                        "error": "强制分配任务失败",
                        "task_id": task_context.task_id,
                        "debug_info": forced_result
                    }
        
        # 等待所有分配的智能体完成
        await self._wait_for_agents_completion(task_context)
        
        # 收集智能体执行结果
        await self._collect_agent_conversations(task_context)
        
        # 检查是否需要继续协调
        continuation_needed = await self._check_coordination_continuation(task_context)
        
        if continuation_needed:
            self.logger.info(f"🔄 需要继续协调 - 分析智能体结果并决定下一步")
            
            # 构建继续协调的任务描述
            continuation_task = await self._build_continuation_task(task_context)
            
            # 继续执行协调（分析结果 + 下一步决策）
            continuation_result = await self.process_with_function_calling(
                user_request=continuation_task,
                max_iterations=max_iterations,
                conversation_id=f"{conversation_id}_continuation",
                preserve_context=True,
                enable_self_continuation=True,
                max_self_iterations=2
            )
            
            # 记录继续协调的结果
            task_context.add_conversation_message(
                role="assistant",
                content=continuation_result,
                agent_id=self.agent_id,
                metadata={"type": "coordination_continuation", "task_stage": "analysis"}
            )
            
            # 递归调用，直到所有协调完成
            return await self._run_coordination_loop(task_context, continuation_result, conversation_id, max_iterations)
        else:
            self.logger.info(f"✅ 协调循环完成 - 任务ID: {task_context.task_id}")
            return self._collect_final_result(task_context, initial_result)
    
    async def _wait_for_agents_completion(self, task_context: TaskContext):
        """等待所有分配的智能体完成任务"""
        max_wait_time = 300  # 最大等待5分钟
        check_interval = 2   # 每2秒检查一次
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # 检查所有分配的智能体是否完成
            all_completed = True
            for agent_id in task_context.agent_results.keys():
                if agent_id in self.registered_agents:
                    agent_info = self.registered_agents[agent_id]
                    if agent_info.status != AgentStatus.IDLE:
                        all_completed = False
                        break
            
            if all_completed:
                self.logger.info(f"✅ 所有智能体执行完成")
                break
                
            # 短暂等待后重新检查
            await asyncio.sleep(check_interval)
        
        if time.time() - start_time >= max_wait_time:
            self.logger.warning(f"⏰ 等待智能体完成超时")
    
    async def _check_coordination_continuation(self, task_context: TaskContext) -> bool:
        """检查是否需要继续协调"""
        # 检查是否有智能体执行结果需要分析
        if not task_context.agent_results:
            self.logger.info(f"🔍 协调继续检查: 没有智能体结果，需要继续协调")
            return True  # 🆕 修改：如果没有智能体结果，说明还没有分配任务，需要继续协调
        
        # 检查是否所有必需的阶段都完成了
        completed_agents = set(task_context.agent_results.keys())
        self.logger.info(f"🔍 协调继续检查: 已完成智能体: {completed_agents}")
        
        # 如果只有Verilog智能体完成，还需要代码审查
        if "enhanced_real_verilog_agent" in completed_agents and "enhanced_real_code_review_agent" not in completed_agents:
            self.logger.info(f"🔍 协调继续检查: 需要代码审查智能体")
            return True
        
        # 如果两个智能体都完成了，检查是否需要最终答案
        if len(completed_agents) >= 2:
            # 检查是否已经提供了最终答案
            for msg in task_context.conversation_history:
                if msg.get("metadata", {}).get("type") == "final_answer":
                    self.logger.info(f"🔍 协调继续检查: 已有最终答案，无需继续")
                    return False
            self.logger.info(f"🔍 协调继续检查: 需要提供最终答案")
            return True
        
        self.logger.info(f"🔍 协调继续检查: 所有任务已完成")
        return False
        return False
    
    async def _build_continuation_task(self, task_context: TaskContext) -> str:
        """构建继续协调的任务描述"""
        # 获取智能体执行结果
        results_summary = []
        for agent_id, result_info in task_context.agent_results.items():
            if isinstance(result_info, dict) and 'response' in result_info:
                results_summary.append(f"- {agent_id}: {result_info.get('response', 'Unknown')[:200]}...")
        
        results_text = "\n".join(results_summary) if results_summary else "无智能体结果"
        
        # 🔧 修正3: 强制执行设计→验证两阶段流程
        completed_agents = set(task_context.agent_results.keys())
        workflow_stage = self._determine_workflow_stage(completed_agents)
        
        # 🔧 修复：检查是否有工具执行失败的情况
        failed_tools = []
        for tool_exec in task_context.tool_executions:
            if not tool_exec.get("success", True):
                failed_tools.append(f"- {tool_exec.get('tool_name')}: {tool_exec.get('error', 'Unknown error')}")
        
        failed_tools_text = "\n".join(failed_tools) if failed_tools else "无失败的工具调用"
        
        # 根据工作流阶段和失败情况生成不同的协调指导
        if workflow_stage == "initial" and failed_tools:
            # 🔧 修复：处理初始阶段工具调用失败的情况
            coordination_guide = f"""
**🚨 紧急修复 - 工具调用失败**:
检测到以下工具调用失败：
{failed_tools_text}

**修复策略**:
1. 如果 `assign_task_to_agent` 失败，必须重新调用该工具
2. 不要调用 `analyze_agent_result`，因为没有可分析的结果
3. 确保 `assign_task_to_agent` 参数正确：
   - agent_id: "enhanced_real_verilog_agent"
   - task_description: 完整的任务描述
   - 不要包含 task_id 参数（该工具不支持此参数）

**重要**: 必须先成功分配任务，然后才能分析结果"""
        
        elif workflow_stage == "design_completed":
            coordination_guide = """
**🚨 强制工作流程 - 设计阶段已完成**:
1. 首先调用 `analyze_agent_result` 分析Verilog设计智能体的结果
2. **强制下一步**: 无论分析结果如何，都必须进入验证阶段
3. 必须调用 `assign_task_to_agent` 分配任务给 `enhanced_real_code_review_agent`
4. 任务描述应包含：审查设计代码、生成测试台、执行仿真验证

**重要**: 这是强制的两阶段流程，设计完成后必须进行验证"""
        
        elif workflow_stage == "verification_completed":
            coordination_guide = """
**🎯 工作流程 - 验证阶段已完成**:
1. 首先调用 `analyze_agent_result` 分析代码审查智能体的结果
2. 调用 `check_task_completion` 检查整体任务完成状态
3. 如果任务完整，调用 `provide_final_answer` 提供最终答案"""
        
        else:
            # 默认情况
            coordination_guide = """
**协调要求**:
1. 首先调用 `analyze_agent_result` 分析已完成智能体的结果质量
2. 基于分析结果决定下一步行动:
   - 如果是设计阶段完成，必须分配给代码审查智能体进行验证
   - 如果是验证阶段完成，调用 `check_task_completion`
   - 如果两个阶段都完成，调用 `provide_final_answer`
   - 如果质量不满足要求，重新分配给同一智能体改进"""
        
        return f"""🔄 协调任务继续 - 分析智能体执行结果并决定下一步

**当前任务状态**:
- 任务ID: {task_context.task_id}
- 已完成的智能体: {list(task_context.agent_results.keys())}
- 工作流阶段: {workflow_stage}
- 执行结果摘要:
{results_text}

**工具执行状态**:
- 失败的工具调用:
{failed_tools_text}

**当前阶段**: 结果分析与下一步决策

{coordination_guide}

请严格按照协调流程执行，必须调用相应的分析和决策工具。
"""
    
    def _determine_workflow_stage(self, completed_agents: Set[str]) -> str:
        """确定当前工作流阶段"""
        
        if "enhanced_real_verilog_agent" in completed_agents and "enhanced_real_code_review_agent" not in completed_agents:
            # Verilog设计完成，但代码审查未完成
            return "design_completed"
        elif "enhanced_real_code_review_agent" in completed_agents:
            # 代码审查已完成（可能两个都完成了）
            return "verification_completed"
        elif len(completed_agents) == 0:
            # 还没有智能体完成
            return "initial"
        else:
            # 其他情况
            return "unknown"
    
    # =============================================================================
    # 实现抽象方法
    # =============================================================================
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """调用LLM进行Function Calling - 包含格式修复"""
        try:
            # 使用统一的LLM通信模块
            result = await self.llm_manager.call_llm_for_function_calling(
                conversation, 
                system_prompt_builder=self._build_enhanced_system_prompt
            )
            
            # 🔧 应用格式修复 - 修复协调器的工具调用格式问题
            result = self._fix_tool_call_format(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Function Calling调用失败: {e}")
            return f"错误: {str(e)}"
    
    async def _call_llm_traditional(self, conversation: List[Dict[str, str]]) -> str:
        """传统LLM调用方法"""
        try:
            # 使用统一的LLM通信模块
            return await self.llm_manager.call_llm_traditional(
                conversation,
                system_prompt_builder=self._build_enhanced_system_prompt
            )
            
        except Exception as e:
            self.logger.error(f"❌ 传统LLM调用失败: {e}")
            return f"错误: {str(e)}"
    
    def get_capabilities(self) -> Set[AgentCapability]:
        """获取智能体能力"""
        return {
            AgentCapability.TASK_COORDINATION,
            AgentCapability.INTELLIGENT_ROUTING,
            AgentCapability.CONTEXT_MANAGEMENT,
            AgentCapability.DECISION_MAKING
        }
    
    def get_specialty_description(self) -> str:
        """获取智能体专业描述"""
        return "基于LLM的智能协调智能体，负责任务分析和智能体分配"
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message: TaskMessage,
                                  file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """执行增强任务"""
        task_id = original_message.task_id
        self.logger.info(f"🎯 开始执行协调任务: {task_id}")
        
        try:
            # 使用协调任务执行
            result = await self.coordinate_task(
                user_request=enhanced_prompt,
                conversation_id=original_message.task_id,
                max_iterations=10
            )
            
            return {
                "success": result.get("success", False),
                "task_id": task_id,
                "response": result.get("coordination_result", ""),
                "agent_results": result.get("agent_results", {}),
                "execution_summary": result.get("execution_summary", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ 协调任务执行异常: {task_id} - {str(e)}")
            return {
                "success": False,
                "task_id": task_id,
                "error": f"执行异常: {str(e)}"
            } 

    async def _tool_identify_task_type(self, user_request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """智能识别任务类型"""
        try:
            self.logger.info(f"🔍 识别任务类型: {user_request[:100]}...")
            
            # 使用模式匹配识别任务类型
            task_type = self._classify_task_by_patterns(user_request)
            
            # 使用LLM进行深度分析
            llm_analysis = await self._analyze_task_with_llm(user_request, task_type)
            
            # 合并结果
            final_task_type = llm_analysis.get("task_type", task_type)
            confidence = llm_analysis.get("confidence", 0.7)
            
            # 确定优先级
            priority = self._determine_task_priority(user_request, final_task_type)
            
            return {
                "success": True,
                "task_type": final_task_type.value if isinstance(final_task_type, TaskType) else final_task_type,
                "confidence": confidence,
                "priority": priority.value if isinstance(priority, TaskPriority) else priority,
                "analysis": llm_analysis.get("analysis", ""),
                "keywords": llm_analysis.get("keywords", []),
                "suggested_agent": self._get_suggested_agent(final_task_type)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 任务类型识别失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "task_type": "unknown",
                "confidence": 0.0,
                "priority": "medium"
            }
    
    def _classify_task_by_patterns(self, user_request: str) -> TaskType:
        """使用模式匹配分类任务"""
        request_lower = user_request.lower()
        
        # 计算每种任务类型的匹配分数
        scores = {}
        for task_type, patterns in self.task_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, request_lower):
                    score += 1
            scores[task_type] = score
        
        # 找到最高分数的任务类型
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                for task_type, score in scores.items():
                    if score == max_score:
                        return task_type
        
        return TaskType.UNKNOWN
    
    async def _analyze_task_with_llm(self, user_request: str, initial_task_type: TaskType) -> Dict[str, Any]:
        """使用LLM深度分析任务"""
        try:
            analysis_prompt = f"""
请深度分析以下用户请求，识别任务类型和特征：

用户请求: {user_request}
初步分类: {initial_task_type.value}

请从以下方面进行分析：
1. 任务类型（design/verification/analysis/debug/composite）
2. 任务复杂度（simple/medium/complex）
3. 关键特征和需求
4. 建议的智能体选择
5. 置信度评分（0-1）

请返回JSON格式的分析结果。
"""
            
            # 使用统一的LLM管理器进行调用
            conversation = [
                {"role": "system", "content": "你是任务分析专家，请提供准确的任务类型识别。"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.llm_manager.call_llm_for_function_calling(conversation)
            
            # 尝试解析JSON响应
            try:
                analysis = json.loads(response)
                return analysis
            except:
                # 如果解析失败，返回基本分析
                return {
                    "task_type": initial_task_type,
                    "confidence": 0.7,
                    "analysis": response,
                    "keywords": []
                }
                
        except Exception as e:
            self.logger.error(f"❌ LLM任务分析失败: {str(e)}")
            return {
                "task_type": initial_task_type,
                "confidence": 0.5,
                "analysis": f"分析失败: {str(e)}",
                "keywords": []
            }
    
    def _determine_task_priority(self, user_request: str, task_type: TaskType) -> TaskPriority:
        """确定任务优先级"""
        request_lower = user_request.lower()
        
        # 高优先级关键词
        high_priority_keywords = [
            "紧急", "urgent", "立即", "immediately", "重要", "important",
            "关键", "critical", "优先", "priority", "快速", "quick"
        ]
        
        # 低优先级关键词
        low_priority_keywords = [
            "不急", "not urgent", "慢慢", "slowly", "可选", "optional",
            "次要", "secondary", "低优先级", "low priority"
        ]
        
        # 检查优先级关键词
        for keyword in high_priority_keywords:
            if keyword in request_lower:
                return TaskPriority.HIGH
        
        for keyword in low_priority_keywords:
            if keyword in request_lower:
                return TaskPriority.LOW
        
        # 根据任务类型确定默认优先级
        if task_type == TaskType.DEBUG:
            return TaskPriority.HIGH  # 调试任务通常优先级较高
        elif task_type == TaskType.ANALYSIS:
            return TaskPriority.LOW   # 分析任务通常优先级较低
        
        return TaskPriority.MEDIUM
    
    def _get_suggested_agent(self, task_type: TaskType) -> str:
        """根据任务类型获取建议的智能体"""
        if task_type == TaskType.DESIGN:
            return "enhanced_real_verilog_agent"
        elif task_type in [TaskType.VERIFICATION, TaskType.ANALYSIS, TaskType.DEBUG]:
            return "enhanced_real_code_review_agent"
        else:
            return "enhanced_real_verilog_agent"  # 默认选择设计智能体
    
    async def _tool_recommend_agent(self, task_type: str, task_description: str,
                                  priority: str = "medium", constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """推荐最合适的智能体"""
        try:
            self.logger.info(f"🤖 推荐智能体: {task_type} - {priority}")
            
            # 获取可用智能体
            available_agents = self._get_available_agents()
            
            if not available_agents:
                return {
                    "success": False,
                    "error": "没有可用的智能体"
                }
            
            # 根据任务类型过滤智能体
            suitable_agents = self._filter_agents_by_task_type(available_agents, task_type)
            
            if not suitable_agents:
                return {
                    "success": False,
                    "error": f"没有适合任务类型 '{task_type}' 的智能体"
                }
            
            # 计算智能体评分
            agent_scores = self._calculate_agent_scores(suitable_agents, task_type, priority, constraints)
            
            # 选择最高分的智能体
            best_agent = max(agent_scores.items(), key=lambda x: x[1])
            
            return {
                "success": True,
                "recommended_agent": best_agent[0],
                "score": best_agent[1],
                "all_scores": agent_scores,
                "reasoning": self._generate_recommendation_reasoning(best_agent[0], best_agent[1], task_type),
                "alternative_agents": self._get_alternative_agents(agent_scores, best_agent[0])
            }
            
        except Exception as e:
            self.logger.error(f"❌ 智能体推荐失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_available_agents(self) -> List[Tuple[str, AgentInfo]]:
        """获取可用智能体列表"""
        available = []
        for agent_id, agent_info in self.registered_agents.items():
            if agent_info.status == AgentStatus.IDLE:
                available.append((agent_id, agent_info))
        return available
    
    def _filter_agents_by_task_type(self, agents: List[Tuple[str, AgentInfo]], task_type: str) -> List[Tuple[str, AgentInfo]]:
        """根据任务类型过滤智能体"""
        filtered = []
        
        for agent_id, agent_info in agents:
            # 检查智能体是否适合该任务类型
            if self._is_agent_suitable_for_task(agent_id, task_type):
                filtered.append((agent_id, agent_info))
        
        return filtered
    
    def _is_agent_suitable_for_task(self, agent_id: str, task_type: str) -> bool:
        """检查智能体是否适合特定任务类型"""
        if task_type == "design":
            return agent_id == "enhanced_real_verilog_agent"
        elif task_type in ["verification", "analysis", "debug"]:
            return agent_id == "enhanced_real_code_review_agent"
        elif task_type == "composite":
            return True  # 复合任务可以使用任何智能体
        else:
            return True  # 未知任务类型允许使用任何智能体
    
    def _calculate_agent_scores(self, agents: List[Tuple[str, AgentInfo]], task_type: str,
                              priority: str, constraints: Dict[str, Any]) -> Dict[str, float]:
        """计算智能体评分"""
        scores = {}
        
        for agent_id, agent_info in agents:
            score = 0.0
            
            # 基础分数
            score += 50.0
            
            # 成功率分数（权重：30%）
            total_tasks = agent_info.success_count + agent_info.failure_count
            if total_tasks > 0:
                success_rate = agent_info.success_count / total_tasks
                score += success_rate * 30.0
            
            # 响应时间分数（权重：20%）
            if agent_info.average_response_time > 0:
                # 响应时间越短，分数越高
                time_score = max(0, 20.0 - (agent_info.average_response_time / 10.0))
                score += time_score
            
            # 连续成功分数（权重：10%）
            consecutive_bonus = min(10.0, agent_info.consecutive_successes * 2.0)
            score += consecutive_bonus
            
            # 优先级匹配分数
            if priority == "high" and agent_info.average_response_time < 30:
                score += 5.0
            
            # 任务类型匹配分数
            if task_type in [task_type.value for task_type in agent_info.preferred_task_types]:
                score += 10.0
            
            # 黑名单惩罚
            if task_type in [task_type.value for task_type in agent_info.blacklisted_task_types]:
                score -= 20.0
            
            scores[agent_id] = max(0.0, score)
        
        return scores
    
    def _generate_recommendation_reasoning(self, agent_id: str, score: float, task_type: str) -> str:
        """生成推荐理由"""
        agent_info = self.registered_agents.get(agent_id)
        if not agent_info:
            return f"推荐 {agent_id}，评分: {score:.1f}"
        
        reasons = []
        
        # 成功率
        total_tasks = agent_info.success_count + agent_info.failure_count
        if total_tasks > 0:
            success_rate = agent_info.success_count / total_tasks
            reasons.append(f"历史成功率: {success_rate:.1%}")
        
        # 响应时间
        if agent_info.average_response_time > 0:
            reasons.append(f"平均响应时间: {agent_info.average_response_time:.1f}秒")
        
        # 连续成功
        if agent_info.consecutive_successes > 0:
            reasons.append(f"连续成功: {agent_info.consecutive_successes}次")
        
        # 任务类型匹配
        if task_type in [task_type.value for task_type in agent_info.preferred_task_types]:
            reasons.append("任务类型匹配")
        
        return f"推荐 {agent_id} (评分: {score:.1f})，理由: {', '.join(reasons)}"
    
    def _get_alternative_agents(self, agent_scores: Dict[str, float], best_agent: str) -> List[str]:
        """获取备选智能体"""
        alternatives = []
        best_score = agent_scores.get(best_agent, 0)
        
        for agent_id, score in agent_scores.items():
            if agent_id != best_agent and score >= best_score * 0.8:  # 分数不低于最佳智能体的80%
                alternatives.append(agent_id)
        
        return alternatives 

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取系统性能摘要"""
        summary = {
            "total_tasks": self.performance_metrics["total_tasks"],
            "successful_tasks": self.performance_metrics["successful_tasks"],
            "failed_tasks": self.performance_metrics["failed_tasks"],
            "success_rate": 0.0,
            "average_completion_time": self.performance_metrics["average_completion_time"],
            "agent_performance": {},
            "system_health": "healthy",
            "recommendations": []
        }
        
        # 计算成功率
        if summary["total_tasks"] > 0:
            summary["success_rate"] = summary["successful_tasks"] / summary["total_tasks"]
        
        # 智能体性能统计
        for agent_id, agent_info in self.registered_agents.items():
            total_tasks = agent_info.success_count + agent_info.failure_count
            success_rate = agent_info.success_count / total_tasks if total_tasks > 0 else 0.0
            
            summary["agent_performance"][agent_id] = {
                "total_tasks": total_tasks,
                "success_rate": success_rate,
                "average_response_time": agent_info.average_response_time,
                "reliability_score": self._calculate_reliability_score(agent_info),
                "status": agent_info.status.value
            }
        
        # 系统健康评估
        system_health = self._assess_system_health()
        summary["system_health"] = system_health["status"]
        summary["recommendations"] = system_health["recommendations"]
        
        return summary
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """评估系统整体健康状态"""
        health = {
            "status": "healthy",
            "issues": [],
            "recommendations": []
        }
        
        # 检查总体成功率
        total_tasks = self.performance_metrics["total_tasks"]
        if total_tasks > 0:
            success_rate = self.performance_metrics["successful_tasks"] / total_tasks
            if success_rate < 0.5:
                health["status"] = "critical"
                health["issues"].append(f"系统成功率过低: {success_rate:.1%}")
                health["recommendations"].append("建议检查智能体配置和系统设置")
            elif success_rate < 0.7:
                health["status"] = "warning"
                health["issues"].append(f"系统成功率偏低: {success_rate:.1%}")
                health["recommendations"].append("建议优化任务分配策略")
        
        # 检查智能体状态
        idle_agents = 0
        working_agents = 0
        for agent_info in self.registered_agents.values():
            if agent_info.status == AgentStatus.IDLE:
                idle_agents += 1
            elif agent_info.status == AgentStatus.WORKING:
                working_agents += 1
        
        if idle_agents == 0:
            health["status"] = "warning"
            health["issues"].append("所有智能体都在工作，可能存在负载过重")
            health["recommendations"].append("考虑添加更多智能体或优化任务分配")
        
        if working_agents == 0 and total_tasks > 0:
            health["status"] = "warning"
            health["issues"].append("没有智能体在工作，可能存在配置问题")
            health["recommendations"].append("检查智能体注册和状态")
        
        return health
    
    async def emergency_recovery(self, task_id: str = None) -> Dict[str, Any]:
        """紧急恢复功能"""
        try:
            recovery_result = {
                "success": True,
                "recovered_tasks": [],
                "reset_agents": [],
                "actions_taken": []
            }
            
            # 重置所有智能体状态
            for agent_id, agent_info in self.registered_agents.items():
                if agent_info.status == AgentStatus.WORKING:
                    agent_info.status = AgentStatus.IDLE
                    recovery_result["reset_agents"].append(agent_id)
                    recovery_result["actions_taken"].append(f"重置智能体 {agent_id} 状态")
            
            # 恢复特定任务或所有任务
            if task_id:
                if task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    task.assigned_agent = None
                    task.current_stage = "recovered"
                    task.retry_count += 1
                    recovery_result["recovered_tasks"].append(task_id)
                    recovery_result["actions_taken"].append(f"恢复任务 {task_id}")
            else:
                # 恢复所有活跃任务
                for tid, task in self.active_tasks.items():
                    task.assigned_agent = None
                    task.current_stage = "recovered"
                    task.retry_count += 1
                    recovery_result["recovered_tasks"].append(tid)
                recovery_result["actions_taken"].append("恢复所有活跃任务")
            
            self.logger.info(f"🚨 紧急恢复完成: {len(recovery_result['recovered_tasks'])} 个任务, {len(recovery_result['reset_agents'])} 个智能体")
            
            return recovery_result
            
        except Exception as e:
            self.logger.error(f"❌ 紧急恢复失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_status_report(self) -> Dict[str, Any]:
        """获取系统状态报告"""
        report = {
            "timestamp": time.time(),
            "system_info": {
                "coordinator_id": self.agent_id,
                "version": "enhanced_v2.0",
                "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
            },
            "agent_status": {},
            "task_status": {},
            "performance_metrics": self.get_performance_summary(),
            "system_health": self._assess_system_health(),
            "recommendations": []
        }
        
        # 智能体状态
        for agent_id, agent_info in self.registered_agents.items():
            report["agent_status"][agent_id] = {
                "status": agent_info.status.value,
                "specialty": agent_info.specialty,
                "capabilities": [cap.value for cap in agent_info.capabilities],
                "performance": self._calculate_agent_performance_metrics(agent_info),
                "health": self._assess_agent_health(agent_info)
            }
        
        # 任务状态
        for task_id, task in self.active_tasks.items():
            report["task_status"][task_id] = {
                "stage": task.current_stage,
                "assigned_agent": task.assigned_agent,
                "iteration_count": task.iteration_count,
                "retry_count": task.retry_count,
                "completion_status": task.completion_status,
                "quality_score": task.quality_score,
                "execution_time": time.time() - task.start_time
            }
        
        # 生成建议
        recommendations = []
        
        # 基于性能指标的建议
        if report["performance_metrics"]["success_rate"] < 0.7:
            recommendations.append("系统成功率偏低，建议优化任务分配策略")
        
        # 基于智能体状态的建议
        idle_count = sum(1 for agent in self.registered_agents.values() if agent.status == AgentStatus.IDLE)
        if idle_count == 0:
            recommendations.append("所有智能体都在工作，考虑添加更多智能体")
        
        # 基于任务状态的建议
        stuck_tasks = [tid for tid, task in self.active_tasks.items() if task.retry_count > 3]
        if stuck_tasks:
            recommendations.append(f"发现 {len(stuck_tasks)} 个卡住的任务，建议进行紧急恢复")
        
        report["recommendations"] = recommendations
        
        return report
    
    def optimize_agent_allocation(self) -> Dict[str, Any]:
        """优化智能体分配策略"""
        optimization_result = {
            "success": True,
            "optimizations": [],
            "agent_recommendations": {}
        }
        
        # 分析智能体性能
        for agent_id, agent_info in self.registered_agents.items():
            recommendations = []
            
            # 基于成功率的优化
            total_tasks = agent_info.success_count + agent_info.failure_count
            if total_tasks > 0:
                success_rate = agent_info.success_count / total_tasks
                if success_rate < 0.5:
                    recommendations.append("成功率过低，建议检查配置或重新训练")
                elif success_rate < 0.7:
                    recommendations.append("成功率偏低，建议优化prompt或参数")
            
            # 基于响应时间的优化
            if agent_info.average_response_time > 60:
                recommendations.append("响应时间过长，建议优化性能或检查网络")
            
            # 基于连续失败的优化
            if agent_info.consecutive_failures > 2:
                recommendations.append("连续失败次数过多，建议重启或更换智能体")
            
            if recommendations:
                optimization_result["agent_recommendations"][agent_id] = recommendations
                optimization_result["optimizations"].extend(recommendations)
        
        # 负载均衡优化
        working_agents = [aid for aid, info in self.registered_agents.items() if info.status == AgentStatus.WORKING]
        idle_agents = [aid for aid, info in self.registered_agents.items() if info.status == AgentStatus.IDLE]
        
        if len(working_agents) > len(idle_agents):
            optimization_result["optimizations"].append("工作智能体过多，建议优化任务分配策略")
        
        return optimization_result
    
    async def _tool_provide_final_answer(self, final_summary: str, task_status: str, results_summary: Dict = None) -> Dict[str, Any]:
        """这是一个虚拟工具，它的作用是格式化最终输出，并标记任务流程的结束。"""
        self.logger.info(f"🏁 任务完成，提供最终答案: {final_summary[:100]}...")
        # 在实际应用中，这个函数可以直接返回其输入，因为它的主要目的是为了被LLM调用
        return {
            "success": True,
            "final_answer_provided": True,
            "summary": final_summary,
            "status": task_status,
            "results": results_summary or {}
        }

    def _extract_design_file_path_from_previous_results(self) -> Optional[str]:
        """从之前的智能体结果中提取设计文件路径"""
        try:
            # 遍历所有活跃任务
            for task_id, task in self.active_tasks.items():
                # 遍历任务中的智能体结果
                for agent_id, agent_result in task.agent_results.items():
                    # 检查是否是设计智能体的结果
                    if agent_id == "enhanced_real_verilog_agent" and agent_result.get("success", False):
                        # 方法1：直接从 agent_result 中获取 design_file_path
                        if "design_file_path" in agent_result:
                            return agent_result["design_file_path"]
                        
                        # 方法2：从 response 中解析 file_path
                        response = agent_result.get("response", "")
                        if isinstance(response, dict) and "file_path" in response:
                            return response["file_path"]
                        
                        # 方法3：从 response 字符串中提取 file_path
                        if isinstance(response, str):
                            # 尝试从 JSON 格式的响应中提取
                            import re
                            import json
                            
                            # 查找 JSON 格式的 file_path
                            json_pattern = r'"file_path"\s*:\s*"([^"]+)"'
                            match = re.search(json_pattern, response)
                            if match:
                                return match.group(1)
                            
                            # 查找其他可能的路径格式
                            path_patterns = [
                                r'file_path[:\s]+([^\s\n,}]+)',
                                r'path[:\s]+([^\s\n,}]+\.v)',
                                r'saved.*?([^\s\n,}]+\.v)',
                                r'生成.*?([^\s\n,}]+\.v)'
                            ]
                            
                            for pattern in path_patterns:
                                match = re.search(pattern, response, re.IGNORECASE)
                                if match:
                                    path = match.group(1).strip('"\'')
                                    if path.endswith('.v'):
                                        return path
            
            # 如果没有找到，尝试从最近的对话历史中查找
            for task_id, task in self.active_tasks.items():
                for assignment in task.agent_assignments:
                    if assignment.get("design_file_path"):
                        return assignment["design_file_path"]
            
            self.logger.warning("⚠️ 未找到之前的设计文件路径")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 提取设计文件路径时出错: {str(e)}")
            return None
    
    async def _tool_get_tool_usage_guide(self, include_examples: bool = True,
                                       include_best_practices: bool = True) -> Dict[str, Any]:
        """获取LLMCoordinatorAgent专用的工具使用指导"""
        try:
            guide = self._generate_coordinator_tool_guide()
            
            return {
                "success": True,
                "guide": guide,
                "agent_type": "LLMCoordinatorAgent",
                "include_examples": include_examples,
                "include_best_practices": include_best_practices,
                "total_tools": 8,  # LLMCoordinatorAgent有8个工具
                "message": "成功生成LLMCoordinatorAgent的工具使用指导"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 生成工具使用指导失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "生成工具使用指导时发生错误"
            }
    
    def _check_assign_task_called(self, result: str) -> bool:
        """检查是否调用了assign_task_to_agent工具"""
        if not isinstance(result, str) or not result.strip():
            return False
        
        # 提取JSON内容
        json_content = self._extract_json_from_response(result.strip())
        if not json_content:
            return False
            
        try:
            data = json.loads(json_content)
            
            if "tool_calls" in data and isinstance(data["tool_calls"], list):
                for call in data["tool_calls"]:
                    if isinstance(call, dict) and call.get("tool_name") == "assign_task_to_agent":
                        self.logger.info(f"✅ 检测到assign_task_to_agent调用")
                        return True
            
            return False
        except json.JSONDecodeError:
            return False
    
    async def _force_assign_task(self, user_request: str, task_context: TaskContext) -> Dict[str, Any]:
        """强制分配任务给智能体"""
        try:
            self.logger.info(f"🚨 强制分配任务: {user_request[:100]}...")
            
            # 记录强制分配事件
            task_context.add_conversation_message(
                role="system",
                content="检测到LLM未正确调用推荐代理工具，启动强制分配机制",
                agent_id=self.agent_id,
                metadata={"type": "force_assignment", "reason": "missing_recommend_agent"}
            )
            
            # 分析任务类型
            task_analysis = await self._tool_identify_task_type(user_request)
            if not task_analysis.get("success", False):
                return {"success": False, "error": "任务类型识别失败"}
            
            task_type = task_analysis.get("task_type", "design")
            
            # 记录任务类型识别结果
            task_context.add_conversation_message(
                role="system",
                content=f"强制识别任务类型: {task_type}",
                agent_id=self.agent_id,
                metadata={"type": "task_type_identification", "task_type": task_type}
            )
            
            # 推荐智能体
            agent_recommendation = await self._tool_recommend_agent(
                task_type=task_type,
                task_description=user_request,
                priority="medium"
            )
            
            if not agent_recommendation.get("success", False):
                return {"success": False, "error": "智能体推荐失败"}
            
            recommended_agent = agent_recommendation.get("recommended_agent", "enhanced_real_verilog_agent")
            recommendation_score = agent_recommendation.get("score", 0)
            
            # 记录智能体推荐结果
            task_context.add_conversation_message(
                role="system",
                content=f"强制推荐智能体: {recommended_agent} (评分: {recommendation_score:.1f})",
                agent_id=self.agent_id,
                metadata={"type": "agent_recommendation", "agent_id": recommended_agent, "score": recommendation_score}
            )
            
            # 强制分配任务
            assign_result = await self._tool_assign_task_to_agent(
                agent_id=recommended_agent,
                task_description=user_request,
                expected_output="生成完整的Verilog代码文件",
                task_type=task_type,
                priority="medium"
            )
            
            # 记录任务分配结果
            if assign_result.get("success", False):
                self.logger.info(f"✅ 强制分配任务成功: {recommended_agent}")
                task_context.add_conversation_message(
                    role="system",
                    content=f"强制分配任务成功: {recommended_agent}",
                    agent_id=self.agent_id,
                    metadata={"type": "task_assignment", "agent_id": recommended_agent, "success": True}
                )
                return {"success": True, "agent_id": recommended_agent, "result": assign_result}
            else:
                self.logger.error(f"❌ 强制分配任务失败: {assign_result.get('error', '未知错误')}")
                task_context.add_conversation_message(
                    role="system",
                    content=f"强制分配任务失败: {assign_result.get('error')}",
                    agent_id=self.agent_id,
                    metadata={"type": "task_assignment", "success": False, "error": assign_result.get('error')}
                )
                return {"success": False, "error": assign_result.get("error", "分配任务失败")}
                
        except Exception as e:
            self.logger.error(f"❌ 强制分配任务异常: {str(e)}")
            return {"success": False, "error": str(e)}