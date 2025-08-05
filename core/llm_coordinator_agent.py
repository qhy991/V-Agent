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
        
        # 初始化LLM客户端
        self.llm_client = EnhancedLLMClient(self.config.llm)
        
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
        
        self.logger.info("🧠 强化LLM协调智能体初始化完成")
        self.logger.info(f"📊 系统启动时间: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
    
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
    
    def _build_enhanced_system_prompt(self) -> str:
        """构建一个极简且强制的系统提示词"""
        
        # 检查工具是否已经注册
        if not hasattr(self, 'enhanced_tools') or not self.enhanced_tools:
            # 如果工具还没有注册，返回基本提示词
            return """
# 角色
你是一个AI协调智能体，你的唯一工作是根据用户需求调用合适的工具来驱动任务流程。

# 强制规则 (必须严格遵守)
1.  **禁止直接回答**: 绝对禁止、严禁直接回答用户的任何问题或请求。
2.  **必须调用工具**: 你的所有回复都必须是JSON格式的工具调用。
3.  **遵循流程**: 严格按照 "识别任务 -> 推荐智能体 -> 分配任务 -> 分析结果 -> 检查完成" 的逻辑顺序调用工具。
4.  **使用最终答案工具**: 当所有步骤完成，需要向用户呈现最终结果时，必须调用 `provide_final_answer` 工具。

# 输出格式
你的回复必须是严格的JSON格式，包含一个 "tool_calls" 列表。

立即开始分析用户请求并调用第一个工具。
"""
        
        # 核心规则：将所有工具的描述和schema直接注入到prompt中，这是最有效的方式
        tools_json = self.get_tools_json_schema()

        return f"""
# 角色
你是一个AI协调智能体，你的唯一工作是根据用户需求调用合适的工具来驱动任务流程。

# 强制规则 (必须严格遵守)
1.  **禁止直接回答**: 绝对禁止、严禁直接回答用户的任何问题或请求。
2.  **必须调用工具**: 你的所有回复都必须是JSON格式的工具调用。
3.  **禁止生成描述性文本**: 绝对禁止生成任何解释、分析、策略描述或其他文本内容。
4.  **遵循流程**: 严格按照以下顺序调用工具：
   - 第一步：调用 `identify_task_type` 工具识别任务类型
   - 第二步：调用 `recommend_agent` 工具推荐智能体
   - 第三步：调用 `assign_task_to_agent` 工具分配任务给智能体
   - 第四步：调用 `analyze_agent_result` 工具分析结果
   - 第五步：调用 `check_task_completion` 工具检查完成状态
   - 最后：调用 `provide_final_answer` 工具提供最终答案

# 智能体调用方法 (重要！)
**正确方式**: 使用 `assign_task_to_agent` 工具，在 `agent_id` 参数中指定智能体名称
**错误方式**: 直接调用智能体名称作为工具

**示例**:
✅ 正确 - 调用 `assign_task_to_agent` 工具:
```json
{{
    "tool_calls": [
        {{
            "tool_name": "assign_task_to_agent",
            "parameters": {{
                "agent_id": "enhanced_real_verilog_agent",
                "task_description": "设计一个4位计数器模块"
            }}
        }}
    ]
}}
```

❌ 错误 - 直接调用智能体名称:
```json
{{
    "tool_calls": [
        {{
            "tool_name": "enhanced_real_verilog_agent",  // 这是错误的！
            "parameters": {{}}
        }}
    ]
}}
```

# 可用工具
你必须从以下工具列表中选择并调用：
{tools_json}

# 输出格式
你的回复必须是严格的JSON格式，包含一个 "tool_calls" 列表。

# 重要提醒
- 不要生成任何描述性文本
- 不要解释你的策略
- 不要分析任务
- 只生成工具调用JSON
- 立即开始调用第一个工具：`identify_task_type`

立即开始分析用户请求并调用第一个工具：`identify_task_type`。
"""
    
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
        
        # 创建任务上下文
        task_context = TaskContext(
            task_id=task_id,
            original_request=user_request,
            max_iterations=max_iterations
        )
        
        # 如果提供了外部testbench，添加到任务上下文
        if external_testbench_path:
            task_context.external_testbench_path = external_testbench_path
            self.logger.info(f"📁 使用外部testbench: {external_testbench_path}")
        
        self.active_tasks[task_id] = task_context
        
        try:
            # 构建协调任务
            coordination_task = self._build_coordination_task(user_request, task_context)
            
            # 使用Function Calling执行协调
            result = await self.process_with_function_calling(
                user_request=coordination_task,
                max_iterations=max_iterations,
                conversation_id=conversation_id,
                preserve_context=True,
                enable_self_continuation=True,
                max_self_iterations=3
            )
            
            # 🔍 检查是否实际调用了工具
            if not self._has_executed_tools(result):
                self.logger.warning("⚠️ 协调智能体没有调用任何工具，强制重新执行")
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
            
            # 收集最终结果
            final_result = self._collect_final_result(task_context, result)
            
            self.logger.info(f"✅ 任务协调完成: {task_id}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"❌ 任务协调失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
        finally:
            # 清理任务上下文
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    def _has_executed_tools(self, result: str) -> bool:
        """检查LLM的回复是否是一个有效的工具调用JSON。"""
        if not isinstance(result, str) or not result.strip().startswith('{'):
            return False
        try:
            data = json.loads(result)
            if "tool_calls" in data and isinstance(data["tool_calls"], list) and len(data["tool_calls"]) > 0:
                # 进一步检查tool_calls列表中的元素是否合法
                call = data["tool_calls"][0]
                if "tool_name" in call and "parameters" in call:
                    return True
            return False
        except json.JSONDecodeError:
            return False
    
    def _build_forced_coordination_task(self, user_request: str, task_context: TaskContext) -> str:
        """构建一个极度强制的协调任务，只要求调用第一个工具。"""
        
        # 获取第一个必须调用的工具信息
        first_tool_schema = self.get_tool_schema("identify_task_type")

        return f"""
# 强制指令
你必须立即调用 `identify_task_type` 工具。

**用户需求**:
{user_request}

# 工具调用格式 (必须严格遵守):
```json
{{
    "tool_calls": [
        {{
            "tool_name": "identify_task_type",
            "parameters": {{
                "user_request": "{user_request.replace('"', '\\"')}"
            }}
        }}
    ]
}}
```

# 重要提醒
- 只能调用 `identify_task_type` 工具
- 不要直接调用智能体名称
- 不要生成任何其他内容
- 不要生成任何描述性文本
- 不要解释你的策略
- 不要分析任务
- 只生成工具调用JSON

不要回复任何其他内容，立即生成上述JSON。
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

请根据用户需求和可用智能体能力，制定最优的执行策略并开始协调。
"""
    
    async def _tool_assign_task_to_agent(self, agent_id: str, task_description: str,
                                       expected_output: str = "",
                                       task_type: str = "composite",
                                       priority: str = "medium") -> Dict[str, Any]:
        """分配任务给智能体"""
        
        try:
            # 检查智能体是否存在
            if agent_id not in self.registered_agents:
                return {
                    "success": False,
                    "error": f"智能体不存在: {agent_id}"
                }
            
            agent_info = self.registered_agents[agent_id]
            agent = agent_info.agent_instance
            
            # 更新智能体状态
            agent_info.status = AgentStatus.WORKING
            agent_info.last_used = time.time()
            
            # 查找当前活跃任务
            current_task = None
            for task_id, task in self.active_tasks.items():
                if task.assigned_agent is None:  # 找到未分配的任务
                    current_task = task
                    break
            
            if current_task:
                current_task.assigned_agent = agent_id
                current_task.current_stage = f"assigned_to_{agent_id}"
                current_task.iteration_count += 1
                
                # 设置智能体的对话ID
                agent_info.conversation_id = f"task_{current_task.task_id}_{agent_id}"
            
            self.logger.info(f"📤 分配任务给智能体 {agent_id}: {task_description[:100]}...")
            
            # 构建增强的任务描述
            enhanced_task = self._build_enhanced_task_description(
                task_description, expected_output, current_task, task_type, priority
            )
            
            # 调用智能体执行任务
            start_time = time.time()
            
            result = await agent.process_with_function_calling(
                user_request=enhanced_task,
                max_iterations=8,
                conversation_id=agent_info.conversation_id,
                preserve_context=True,
                enable_self_continuation=True,
                max_self_iterations=3
            )
            
            execution_time = time.time() - start_time
            
            # 更新智能体统计
            if result and len(result) > 0:
                agent_info.success_count += 1
            else:
                agent_info.failure_count += 1
            
            # 恢复智能体状态
            agent_info.status = AgentStatus.IDLE
            
            # 保存结果到任务上下文
            if current_task:
                current_task.agent_results[agent_id] = {
                    "result": result,
                    "execution_time": execution_time,
                    "timestamp": time.time()
                }
            
            return {
                "success": True,
                "agent_id": agent_id,
                "result": result,
                "execution_time": execution_time,
                "agent_specialty": agent_info.specialty
            }
            
        except Exception as e:
            self.logger.error(f"❌ 任务分配失败: {str(e)}")
            
            # 恢复智能体状态
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id].status = AgentStatus.IDLE
                self.registered_agents[agent_id].failure_count += 1
            
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }
    
    def _build_enhanced_task_description(self, task_description: str, 
                                       expected_output: str,
                                       task_context: TaskContext = None,
                                       task_type: str = "composite",
                                       priority: str = "medium") -> str:
        """构建增强的任务描述"""
        
        # 构建外部testbench信息
        external_testbench_section = ""
        if task_context and hasattr(task_context, 'external_testbench_path') and task_context.external_testbench_path:
            external_testbench_section = f"""

**🎯 外部Testbench模式**:
- 外部testbench路径: {task_context.external_testbench_path}
- 工作指导: 如果你是代码审查智能体，请直接使用提供的testbench进行测试，不要生成新的testbench
- 专注任务: 代码审查、错误修复、测试执行和结果分析"""
        
        enhanced_task = f"""
📋 协调智能体分配的任务

**任务描述**:
{task_description}

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

**执行要求**:
1. 仔细分析任务需求
2. 生成高质量的代码
3. 提供详细的说明文档
4. 确保代码可读性和可维护性
5. 如有需要，生成相应的测试台（除非已提供外部testbench）

请开始执行任务。
"""
        return enhanced_task
    
    async def _tool_analyze_agent_result(self, agent_id: str, result: Dict[str, Any],
                                       task_context: Dict[str, Any] = None,
                                       quality_threshold: float = 80.0) -> Dict[str, Any]:
        """增强的智能体执行结果分析"""
        
        try:
            self.logger.info(f"🔍 深度分析智能体 {agent_id} 的执行结果")
            
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
        """增强的结果质量分析"""
        
        analysis = {
            "quality_score": 0.0,
            "completeness": "unknown",
            "issues": [],
            "strengths": [],
            "recommendations": [],
            "detailed_metrics": {},
            "risk_assessment": "low"
        }
        
        # 检查结果是否为空
        if not result or not result.get("success", False):
            analysis["completeness"] = "failed"
            analysis["issues"].append("任务执行失败")
            analysis["recommendations"].append("重新分配任务或更换智能体")
            analysis["risk_assessment"] = "high"
            return analysis
        
        # 分析结果内容
        content = result.get("content", "")
        if not content:
            analysis["completeness"] = "incomplete"
            analysis["issues"].append("结果内容为空")
            analysis["recommendations"].append("要求智能体重新执行并提供详细结果")
            analysis["risk_assessment"] = "medium"
            return analysis
        
        # 详细质量指标分析
        detailed_metrics = self._analyze_detailed_metrics(content, result)
        analysis["detailed_metrics"] = detailed_metrics
        
        # 计算综合质量分数
        quality_score = self._calculate_comprehensive_quality_score(detailed_metrics)
        analysis["quality_score"] = quality_score
        
        # 根据质量分数判断完整性
        if quality_score >= quality_threshold:
            analysis["completeness"] = "complete"
            analysis["risk_assessment"] = "low"
        elif quality_score >= quality_threshold * 0.7:
            analysis["completeness"] = "partial"
            analysis["risk_assessment"] = "medium"
        else:
            analysis["completeness"] = "incomplete"
            analysis["risk_assessment"] = "high"
        
        # 生成具体建议
        analysis["recommendations"] = self._generate_specific_recommendations(detailed_metrics, quality_score, quality_threshold)
        
        return analysis
    
    def _analyze_detailed_metrics(self, content: str, result: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _calculate_comprehensive_quality_score(self, metrics: Dict[str, float]) -> float:
        """计算综合质量分数"""
        weights = {
            "code_quality": 0.35,
            "documentation_quality": 0.20,
            "test_coverage": 0.25,
            "error_handling": 0.10,
            "performance": 0.05,
            "compliance": 0.05
        }
        
        total_score = 0.0
        for metric, weight in weights.items():
            total_score += metrics.get(metric, 0.0) * weight
        
        return min(100.0, total_score)
    
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
        """确定增强的下一步行动"""
        
        completeness = analysis.get("completeness", "unknown")
        quality_score = analysis.get("quality_score", 0)
        risk_assessment = analysis.get("risk_assessment", "low")
        
        # 基于风险等级和完整性决定行动
        if risk_assessment == "high":
            if completeness == "failed":
                return "retry_with_different_agent"
            else:
                return "improve_result"
        
        if completeness == "complete" and quality_score >= 80:
            return "complete_task"
        elif completeness == "partial" and quality_score >= 60:
            return "improve_result"
        elif completeness == "incomplete" or quality_score < 40:
            return "retry_with_different_agent"
        else:
            return "continue_iteration"
    
    def _generate_improvement_suggestions(self, analysis: Dict[str, Any], agent_id: str) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于分析结果生成建议
        if analysis.get("quality_score", 0) < 70:
            suggestions.append("考虑使用不同的智能体重新执行任务")
        
        if "code_quality" in analysis.get("detailed_metrics", {}) and analysis["detailed_metrics"]["code_quality"] < 50:
            suggestions.append("要求智能体提供更详细的代码注释和文档")
        
        if "test_coverage" in analysis.get("detailed_metrics", {}) and analysis["detailed_metrics"]["test_coverage"] < 60:
            suggestions.append("要求生成更全面的测试用例")
        
        # 基于智能体历史表现生成建议
        if agent_id in self.registered_agents:
            agent_info = self.registered_agents[agent_id]
            if agent_info.consecutive_failures > 2:
                suggestions.append("该智能体连续失败次数较多，建议更换智能体")
        
        return suggestions
    
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
        
        # 计算总执行时间
        total_time = 0.0
        success_count = 0
        total_count = len(all_results)
        
        for result in all_results.values():
            execution_time = result.get("execution_time", 0)
            total_time += execution_time
            
            if result.get("success", False):
                success_count += 1
        
        metrics["total_execution_time"] = total_time
        metrics["average_execution_time"] = total_time / total_count if total_count > 0 else 0
        metrics["success_rate"] = success_count / total_count if total_count > 0 else 0
        
        # 计算迭代效率
        if task_context.iteration_count > 0:
            metrics["iteration_efficiency"] = completion_score / task_context.iteration_count
        
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
    
    def _collect_final_result(self, task_context: TaskContext, 
                            coordination_result: str) -> Dict[str, Any]:
        """收集最终结果"""
        
        return {
            "success": True,
            "task_id": task_context.task_id,
            "coordination_result": coordination_result,
            "agent_results": task_context.agent_results,
            "execution_summary": {
                "total_iterations": task_context.iteration_count,
                "assigned_agents": list(task_context.agent_results.keys()),
                "execution_time": time.time() - task_context.start_time
            },
            "conversation_history": task_context.conversation_history
        }
    
    def get_registered_agents(self) -> Dict[str, AgentInfo]:
        """获取已注册的智能体"""
        return self.registered_agents.copy()
    
    def get_active_tasks(self) -> Dict[str, TaskContext]:
        """获取活跃任务"""
        return self.active_tasks.copy()
    
    # =============================================================================
    # 实现抽象方法
    # =============================================================================
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """实现LLM调用 - 使用优化的调用机制避免重复传入system prompt"""
        # 生成对话ID（如果还没有）
        if not hasattr(self, 'current_conversation_id') or not self.current_conversation_id:
            self.current_conversation_id = f"coordinator_agent_{int(time.time())}"
        
        # 构建用户消息
        user_message = ""
        is_first_call = len(conversation) <= 1  # 如果对话历史很少，认为是第一次调用
        
        for msg in conversation:
            if msg["role"] == "user":
                user_message += f"{msg['content']}\n\n"
            elif msg["role"] == "assistant":
                user_message += f"Assistant: {msg['content']}\n\n"
        
        try:
            # 使用优化的LLM调用方法
            response = await self.llm_client.send_prompt_optimized(
                conversation_id=self.current_conversation_id,
                user_message=user_message.strip(),
                system_prompt=self._build_enhanced_system_prompt() if is_first_call else None,
                temperature=0.3,
                max_tokens=4000,
                force_refresh_system=is_first_call
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ 优化LLM调用失败: {str(e)}")
            # 如果优化调用失败，回退到传统方式
            self.logger.warning("⚠️ 回退到传统LLM调用方式")
            return await self._call_llm_traditional(conversation)
    
    async def _call_llm_traditional(self, conversation: List[Dict[str, str]]) -> str:
        """传统的LLM调用方法（作为回退方案）"""
        # 构建完整的prompt
        full_prompt = ""
        system_prompt = self._build_enhanced_system_prompt()
        
        for msg in conversation:
            if msg["role"] == "system":
                system_prompt = msg["content"]  # 覆盖默认system prompt
            elif msg["role"] == "user":
                full_prompt += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                full_prompt += f"Assistant: {msg['content']}\n\n"
        
        try:
            response = await self.llm_client.send_prompt(
                prompt=full_prompt.strip(),
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4000
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ 传统LLM调用失败: {str(e)}")
            raise
    
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
            
            response = await self.llm_client.send_prompt(
                prompt=analysis_prompt,
                system_prompt="你是任务分析专家，请提供准确的任务类型识别。",
                temperature=0.1
            )
            
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