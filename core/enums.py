#!/usr/bin/env python3
"""
枚举和常量定义

Enums and Constants for Centralized Agent Framework
"""

from enum import Enum


class AgentCapability(Enum):
    """智能体能力枚举"""
    CODE_GENERATION = "code_generation"
    TEST_GENERATION = "test_generation"
    CODE_REVIEW = "code_review"
    TASK_COORDINATION = "task_coordination"
    WORKFLOW_MANAGEMENT = "workflow_management"
    SPECIFICATION_ANALYSIS = "specification_analysis"
    MODULE_DESIGN = "module_design"
    VERIFICATION = "verification"
    COVERAGE_ANALYSIS = "coverage_analysis"
    QUALITY_ANALYSIS = "quality_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_GENERATION = "document_generation"
    SYSTEM_MONITORING = "system_monitoring"
    CUSTOM_TASK = "custom_task"


class ConversationState(Enum):
    """对话状态枚举"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    TASK_ANALYSIS = "task_analysis"
    AGENT_SELECTION = "agent_selection"
    TASK_EXECUTION = "task_execution"
    RESULT_REVIEW = "result_review"
    NEXT_SPEAKER_DECISION = "next_speaker_decision"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageType(Enum):
    """消息类型枚举"""
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    COORDINATION_REQUEST = "coordination_request"


class AgentStatus(Enum):
    """智能体状态枚举"""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    OFFLINE = "offline"


class TaskComplexity(Enum):
    """任务复杂度枚举"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class Priority(Enum):
    """优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"