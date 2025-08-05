#!/usr/bin/env python3
"""
基于LLM的协调智能体

LLM-Driven Coordinator Agent
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.base_agent import TaskMessage
from core.enums import AgentCapability, AgentStatus
from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from core.enhanced_logging_config import get_agent_logger


@dataclass
class AgentInfo:
    """智能体信息"""
    agent_id: str
    agent_instance: EnhancedBaseAgent
    capabilities: Set[AgentCapability]
    specialty: str
    status: AgentStatus = AgentStatus.IDLE
    conversation_id: Optional[str] = None
    last_used: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    original_request: str
    current_stage: str = "initial"
    assigned_agent: Optional[str] = None
    agent_results: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    iteration_count: int = 0
    max_iterations: int = 10
    external_testbench_path: Optional[str] = None


class LLMCoordinatorAgent(EnhancedBaseAgent):
    """
    基于LLM的协调智能体
    
    特点：
    1. 将复杂的规则判断逻辑写入system prompt
    2. 智能分析任务并分配给最合适的智能体
    3. 维护长期对话上下文
    4. 支持动态决策和流程调整
    """
    
    def __init__(self, config: FrameworkConfig = None):
        super().__init__(
            agent_id="llm_coordinator_agent",
            role="coordinator",
            capabilities={
                AgentCapability.TASK_COORDINATION,
                AgentCapability.WORKFLOW_MANAGEMENT,
                AgentCapability.SPECIFICATION_ANALYSIS,
                AgentCapability.CODE_REVIEW
            }
        )
        
        # 初始化LLM客户端
        self.config = config or FrameworkConfig.from_env()
        self.llm_client = EnhancedLLMClient(self.config.llm)
        
        # 设置专用日志器
        self.agent_logger = get_agent_logger('LLMCoordinatorAgent')
        
        # 注册的智能体
        self.registered_agents: Dict[str, AgentInfo] = {}
        
        # 任务上下文管理
        self.active_tasks: Dict[str, TaskContext] = {}
        
        # 协调工具
        self._register_coordination_tools()
        
        self.logger.info("🧠 LLM协调智能体初始化完成")
    
    def _register_coordination_tools(self):
        """注册协调工具"""
        
        # 1. 任务分配工具
        self.register_enhanced_tool(
            name="assign_task_to_agent",
            func=self._tool_assign_task_to_agent,
            description="将任务分配给指定的智能体",
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
                        "minLength": 10
                    },
                    "expected_output": {
                        "type": "string",
                        "description": "期望的输出格式和内容",
                        "default": ""
                    }
                },
                "required": ["agent_id", "task_description"]
            }
        )
        
        # 2. 结果分析工具
        self.register_enhanced_tool(
            name="analyze_agent_result",
            func=self._tool_analyze_agent_result,
            description="分析智能体执行结果并决定下一步",
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
                    }
                },
                "required": ["agent_id", "result"]
            }
        )
        
        # 3. 任务完成检查工具
        self.register_enhanced_tool(
            name="check_task_completion",
            func=self._tool_check_task_completion,
            description="检查任务是否完成",
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
                    }
                },
                "required": ["task_id", "all_results", "original_requirements"]
            }
        )
        
        # 4. 智能体状态查询工具
        self.register_enhanced_tool(
            name="query_agent_status",
            func=self._tool_query_agent_status,
            description="查询智能体状态和能力",
            security_level="normal",
            category="coordination",
            schema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "智能体ID",
                        "enum": ["enhanced_real_verilog_agent", "enhanced_real_code_review_agent"]
                    }
                },
                "required": ["agent_id"]
            }
        )
    
    def _build_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词，包含协调逻辑"""
        
        base_prompt = """你是一个智能的协调智能体，负责分析任务并分配给最合适的智能体。

## 🧠 核心职责

1. **任务分析**: 深入分析用户需求，理解任务类型和复杂度
2. **智能体选择**: 根据任务需求选择最合适的智能体
3. **流程协调**: 管理任务执行流程，确保各阶段顺利衔接
4. **质量控制**: 监控执行结果，确保满足用户需求

## 🎯 决策逻辑

### 任务类型识别
- **设计任务**: 需要生成Verilog代码、电路设计、模块实现
- **验证任务**: 需要测试台生成、仿真验证、代码审查
- **分析任务**: 需要代码审查、质量分析、性能优化
- **调试任务**: 需要错误分析、问题修复、代码优化

### 智能体能力匹配
**可用智能体（仅限以下两个）**:
- **enhanced_real_verilog_agent**: 专业的Verilog代码设计和生成，支持模块设计、代码生成、Schema验证
- **enhanced_real_code_review_agent**: 专业的代码审查、测试台生成、仿真验证、质量分析，支持Schema验证

### 智能体选择规则
1. **设计任务** → 选择 `enhanced_real_verilog_agent`
   - Verilog模块设计
   - 代码生成和实现
   - 电路功能设计
   - 参数化设计

2. **验证任务** → 选择 `enhanced_real_code_review_agent`
   - 测试台生成（如无外部testbench提供）
   - 仿真验证（使用外部或生成的testbench）
   - 代码审查
   - 质量分析

3. **复合任务** → 按阶段分配
   - 第一阶段：设计 → `enhanced_real_verilog_agent`
   - 第二阶段：验证 → `enhanced_real_code_review_agent`

### 执行流程决策
1. **单阶段任务**: 直接分配给最合适的智能体
2. **多阶段任务**: 按阶段顺序分配，每阶段完成后评估结果
3. **迭代任务**: 根据结果质量决定是否需要继续迭代
4. **协作任务**: 两个智能体协作完成复杂任务
5. **外部testbench任务**: 当提供外部testbench时，审查智能体跳过testbench生成，直接进行测试验证

## 🔄 协调策略

### 任务分配原则
1. **能力匹配**: 选择能力最匹配的智能体
2. **负载均衡**: 避免单个智能体过载
3. **历史表现**: 考虑智能体的历史成功率
4. **上下文保持**: 优先选择有相关上下文的智能体

### 结果评估标准
1. **功能完整性**: 是否满足所有功能需求
2. **代码质量**: 代码是否规范、可读、可维护
3. **测试覆盖**: 是否有充分的测试验证
4. **错误处理**: 是否处理了边界情况和异常

### 迭代决策逻辑
- **继续迭代**: 结果不完整、质量不达标、有明确改进空间
- **完成任务**: 结果完整、质量达标、满足所有需求
- **切换策略**: 当前方法无效，需要换其他智能体或方法

## 🛠️ 可用工具

1. **assign_task_to_agent**: 分配任务给智能体
2. **analyze_agent_result**: 分析智能体执行结果
3. **check_task_completion**: 检查任务完成状态
4. **query_agent_status**: 查询智能体状态

### 工具调用格式示例：

**assign_task_to_agent** (分配任务):
```json
{
    "tool_calls": [
        {
            "tool_name": "assign_task_to_agent",
            "parameters": {
                "agent_id": "enhanced_real_verilog_agent",
                "task_description": "设计一个8位加法器模块，包含基本加法功能、进位输出、溢出检测",
                "expected_output": "完整的Verilog代码和模块说明"
            }
        }
    ]
}
```

**analyze_agent_result** (分析结果):
```json
{
    "tool_calls": [
        {
            "tool_name": "analyze_agent_result",
            "parameters": {
                "agent_id": "enhanced_real_verilog_agent",
                "result": {
                    "success": true,
                    "code": "module adder8(...)",
                    "execution_time": 15.2
                }
            }
        }
    ]
}
```

**check_task_completion** (检查完成):
```json
{
    "tool_calls": [
        {
            "tool_name": "check_task_completion",
            "parameters": {
                "task_id": "task_1234567890",
                "all_results": {
                    "enhanced_real_verilog_agent": {"result": "..."},
                    "enhanced_real_code_review_agent": {"result": "..."}
                },
                "original_requirements": "设计一个8位加法器模块..."
            }
        }
    ]
}
```

**query_agent_status** (查询状态):
```json
{
    "tool_calls": [
        {
            "tool_name": "query_agent_status",
            "parameters": {
                "agent_id": "enhanced_real_verilog_agent"
            }
        }
    ]
}
```

### 重要参数说明：
- **agent_id**: 必须是 "enhanced_real_verilog_agent" 或 "enhanced_real_code_review_agent"
- **task_description**: 详细的任务描述，至少10个字符
- **task_id**: 任务ID，格式如 "task_1234567890"
- **all_results**: 所有智能体执行结果的汇总对象
- **original_requirements**: 原始任务需求描述字符串

## 📋 执行步骤

1. **分析用户需求**: 理解任务类型、复杂度、期望输出
2. **选择执行策略**: 确定是单阶段、多阶段还是迭代执行
3. **分配任务**: 使用assign_task_to_agent分配任务
4. **监控执行**: 等待智能体完成并返回结果
5. **分析结果**: 使用analyze_agent_result分析结果质量
6. **决策下一步**: 根据分析结果决定继续、完成或调整
7. **完成检查**: 使用check_task_completion确认任务完成

## 🎯 关键原则

- **智能决策**: 基于任务特征和智能体能力做出最优选择
- **上下文保持**: 确保智能体能够获得完整的上下文信息
- **质量优先**: 优先保证结果质量，必要时进行多轮迭代
- **效率平衡**: 在质量和效率之间找到最佳平衡点
- **用户导向**: 始终以用户需求为中心进行决策

## ⚠️ 重要提醒

- **智能体限制**: 只能使用 `enhanced_real_verilog_agent` 和 `enhanced_real_code_review_agent` 两个智能体
- **任务匹配**: 设计任务分配给verilog_agent，验证任务分配给code_review_agent
- **错误处理**: 如果智能体不可用，提供明确的错误信息和替代方案

请根据以上逻辑，智能地协调任务执行流程。"""
        
        # 添加工具信息
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
        
        return base_prompt + tools_info
    
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
                                       expected_output: str = "") -> Dict[str, Any]:
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
                task_description, expected_output, current_task
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
                                       task_context: TaskContext = None) -> str:
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
    
    async def _tool_analyze_agent_result(self, agent_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """分析智能体执行结果"""
        
        try:
            self.logger.info(f"🔍 分析智能体 {agent_id} 的执行结果")
            
            # 分析结果质量
            analysis = self._analyze_result_quality(result, {})
            
            # 确定下一步行动
            next_action = self._determine_next_action(analysis, {})
            
            return {
                "success": True,
                "analysis": analysis,
                "next_action": next_action,
                "agent_id": agent_id
            }
            
        except Exception as e:
            self.logger.error(f"❌ 结果分析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }
    
    def _analyze_result_quality(self, result: Dict[str, Any], 
                              task_context: Dict[str, Any]) -> Dict[str, Any]:
        """分析结果质量"""
        
        analysis = {
            "quality_score": 0,
            "completeness": "unknown",
            "issues": [],
            "strengths": [],
            "recommendations": []
        }
        
        # 检查结果是否为空
        if not result or not result.get("success", False):
            analysis["completeness"] = "failed"
            analysis["issues"].append("任务执行失败")
            analysis["recommendations"].append("重新分配任务或更换智能体")
            return analysis
        
        # 分析结果内容
        content = result.get("content", "")
        if not content:
            analysis["completeness"] = "incomplete"
            analysis["issues"].append("结果内容为空")
            analysis["recommendations"].append("要求智能体重新执行并提供详细结果")
            return analysis
        
        # 检查是否包含代码
        if "module" in content.lower() or "verilog" in content.lower():
            analysis["strengths"].append("包含Verilog代码")
            analysis["quality_score"] += 30
        
        # 检查是否包含测试台
        if "testbench" in content.lower() or "test" in content.lower():
            analysis["strengths"].append("包含测试台")
            analysis["quality_score"] += 20
        
        # 检查是否包含仿真结果
        if "simulation" in content.lower() or "test passed" in content.lower():
            analysis["strengths"].append("包含仿真验证")
            analysis["quality_score"] += 25
        
        # 检查代码质量
        if "//" in content or "/*" in content:
            analysis["strengths"].append("包含注释")
            analysis["quality_score"] += 10
        
        # 检查错误处理
        if "error" in content.lower() and "fix" in content.lower():
            analysis["strengths"].append("包含错误修复")
            analysis["quality_score"] += 15
        
        # 根据质量分数判断完整性
        if analysis["quality_score"] >= 80:
            analysis["completeness"] = "complete"
        elif analysis["quality_score"] >= 50:
            analysis["completeness"] = "partial"
        else:
            analysis["completeness"] = "incomplete"
        
        return analysis
    
    def _determine_next_action(self, analysis: Dict[str, Any], 
                             task_context: Dict[str, Any]) -> str:
        """决定下一步行动"""
        
        completeness = analysis.get("completeness", "unknown")
        quality_score = analysis.get("quality_score", 0)
        
        if completeness == "complete" and quality_score >= 80:
            return "complete_task"
        elif completeness == "partial" and quality_score >= 50:
            return "improve_result"
        elif completeness == "incomplete" or quality_score < 30:
            return "retry_with_different_agent"
        else:
            return "continue_iteration"
    
    async def _tool_check_task_completion(self, task_id: str, 
                                        all_results: Dict[str, Any],
                                        original_requirements: str) -> Dict[str, Any]:
        """检查任务是否完成"""
        
        try:
            # 检查任务是否存在
            if task_id not in self.active_tasks:
                return {
                    "success": False,
                    "error": f"任务不存在: {task_id}"
                }
            
            task_context = self.active_tasks[task_id]
            
            # 分析所有结果
            completion_analysis = self._analyze_task_completion(
                all_results, original_requirements, task_context
            )
            
            return {
                "success": True,
                "is_completed": completion_analysis["is_completed"],
                "completion_score": completion_analysis["completion_score"],
                "missing_requirements": completion_analysis["missing_requirements"],
                "quality_assessment": completion_analysis["quality_assessment"]
            }
            
        except Exception as e:
            self.logger.error(f"❌ 任务完成检查失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_task_completion(self, all_results: Dict[str, Any],
                               original_requirements: str,
                               task_context: TaskContext) -> Dict[str, Any]:
        """分析任务完成情况"""
        
        analysis = {
            "is_completed": False,
            "completion_score": 0,
            "missing_requirements": [],
            "quality_assessment": "unknown"
        }
        
        # 检查是否有结果
        if not all_results:
            analysis["missing_requirements"].append("没有执行结果")
            return analysis
        
        # 分析原始需求
        requirements = original_requirements.lower()
        
        # 检查设计需求
        if "design" in requirements or "module" in requirements:
            if not any("module" in str(result).lower() for result in all_results.values()):
                analysis["missing_requirements"].append("缺少Verilog模块设计")
            else:
                analysis["completion_score"] += 40
        
        # 检查测试需求
        if "test" in requirements or "testbench" in requirements:
            if not any("testbench" in str(result).lower() for result in all_results.values()):
                analysis["missing_requirements"].append("缺少测试台")
            else:
                analysis["completion_score"] += 30
        
        # 检查验证需求
        if "verify" in requirements or "simulation" in requirements:
            if not any("simulation" in str(result).lower() for result in all_results.values()):
                analysis["missing_requirements"].append("缺少仿真验证")
            else:
                analysis["completion_score"] += 30
        
        # 判断是否完成
        if analysis["completion_score"] >= 80 and not analysis["missing_requirements"]:
            analysis["is_completed"] = True
            analysis["quality_assessment"] = "excellent"
        elif analysis["completion_score"] >= 60:
            analysis["quality_assessment"] = "good"
        elif analysis["completion_score"] >= 40:
            analysis["quality_assessment"] = "fair"
        else:
            analysis["quality_assessment"] = "poor"
        
        return analysis
    
    async def _tool_query_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """查询智能体状态"""
        
        try:
            if agent_id not in self.registered_agents:
                return {
                    "success": False,
                    "error": f"智能体不存在: {agent_id}"
                }
            
            agent_info = self.registered_agents[agent_id]
            
            return {
                "success": True,
                "agent_id": agent_id,
                "status": agent_info.status.value,
                "capabilities": [cap.value for cap in agent_info.capabilities],
                "specialty": agent_info.specialty,
                "success_count": agent_info.success_count,
                "failure_count": agent_info.failure_count,
                "last_used": agent_info.last_used,
                "conversation_id": agent_info.conversation_id
            }
            
        except Exception as e:
            self.logger.error(f"❌ 查询智能体状态失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
        """实现LLM调用"""
        try:
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
            
            response = await self.llm_client.send_prompt(
                prompt=full_prompt.strip(),
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=4000
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ LLM调用失败: {str(e)}")
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