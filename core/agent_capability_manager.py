#!/usr/bin/env python3
"""
智能体能力边界管理器
解决任务分配冲突和能力边界模糊问题
"""

import logging
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任务类型枚举"""
    DESIGN = "design"
    VERIFICATION = "verification"
    OPTIMIZATION = "optimization"
    SYNTHESIS = "synthesis"
    SIMULATION = "simulation"
    TESTING = "testing"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"

class AgentRole(Enum):
    """智能体角色枚举"""
    VERILOG_DESIGNER = "verilog_designer"
    CODE_REVIEWER = "code_reviewer"
    TEST_ENGINEER = "test_engineer"
    SYNTHESIS_ENGINEER = "synthesis_engineer"
    COORDINATOR = "coordinator"

@dataclass
class TaskRequirement:
    """任务需求定义"""
    task_type: TaskType
    complexity_level: str  # "simple", "medium", "complex"
    required_tools: List[str] = field(default_factory=list)
    optional_tools: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: Optional[int] = None  # 预估时间（秒）

@dataclass 
class AgentCapability:
    """智能体能力定义"""
    agent_role: AgentRole
    agent_id: str
    supported_tasks: Set[TaskType] = field(default_factory=set)
    available_tools: Set[str] = field(default_factory=set)
    max_complexity: str = "medium"  # "simple", "medium", "complex"
    specializations: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    is_active: bool = True

@dataclass
class TaskAssignment:
    """任务分配结果"""
    task_id: str
    task_requirement: TaskRequirement
    assigned_agent: AgentCapability
    confidence: float
    reasoning: str
    alternatives: List[AgentCapability] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class AgentCapabilityManager:
    """智能体能力边界管理器"""
    
    def __init__(self):
        self.logger = logger
        self.agents: Dict[str, AgentCapability] = {}
        self.task_requirements: Dict[TaskType, TaskRequirement] = {}
        self._initialize_default_capabilities()
        self._initialize_task_requirements()
    
    def _initialize_default_capabilities(self):
        """初始化默认的智能体能力配置"""
        
        # Verilog设计智能体
        self.register_agent(AgentCapability(
            agent_role=AgentRole.VERILOG_DESIGNER,
            agent_id="enhanced_real_verilog_agent",
            supported_tasks={
                TaskType.DESIGN, 
                TaskType.OPTIMIZATION, 
                TaskType.ANALYSIS
            },
            available_tools={
                "write_file", "read_file", "analyze_code_quality",
                "generate_verilog_code", "optimize_verilog_code", 
                "analyze_design_requirements", "search_existing_modules"
            },
            max_complexity="complex",
            specializations=[
                "digital_circuit_design", "parameterized_modules", 
                "state_machines", "arithmetic_units"
            ],
            limitations=[
                "不生成测试台", "不执行仿真", "不进行综合"
            ]
        ))
        
        # 代码审查智能体  
        self.register_agent(AgentCapability(
            agent_role=AgentRole.CODE_REVIEWER,
            agent_id="enhanced_real_code_review_agent",
            supported_tasks={
                TaskType.VERIFICATION,
                TaskType.TESTING,
                TaskType.SIMULATION,
                TaskType.ANALYSIS
            },
            available_tools={
                "generate_testbench", "run_simulation", "analyze_code_quality",
                "write_file", "read_file", "create_build_script"
            },
            max_complexity="complex",
            specializations=[
                "testbench_generation", "simulation_execution",
                "code_quality_analysis", "verification_planning"
            ],
            limitations=[
                "不设计新模块", "不修改设计文件内容"
            ]
        ))
    
    def _initialize_task_requirements(self):
        """初始化任务需求配置"""
        
        self.task_requirements[TaskType.DESIGN] = TaskRequirement(
            task_type=TaskType.DESIGN,
            complexity_level="medium",
            required_tools=["write_file", "generate_verilog_code"],
            optional_tools=["optimize_verilog_code", "analyze_code_quality"],
            prerequisites=["requirement_analysis"]
        )
        
        self.task_requirements[TaskType.VERIFICATION] = TaskRequirement(
            task_type=TaskType.VERIFICATION,
            complexity_level="medium",
            required_tools=["generate_testbench", "run_simulation"],
            optional_tools=["create_build_script", "analyze_code_quality"],
            prerequisites=["design_completion"]
        )
        
        self.task_requirements[TaskType.TESTING] = TaskRequirement(
            task_type=TaskType.TESTING,
            complexity_level="medium",
            required_tools=["generate_testbench", "run_simulation"],
            optional_tools=["create_build_script"],
            prerequisites=["testbench_generation"]
        )
    
    def register_agent(self, capability: AgentCapability):
        """注册智能体能力"""
        self.agents[capability.agent_id] = capability
        self.logger.info(f"📋 注册智能体能力: {capability.agent_id} - {capability.agent_role.value}")
    
    def assign_task(self, task_description: str, task_type: TaskType, 
                   complexity: str = "medium", required_tools: List[str] = None) -> TaskAssignment:
        """智能任务分配"""
        
        # 创建任务需求
        task_req = TaskRequirement(
            task_type=task_type,
            complexity_level=complexity,
            required_tools=required_tools or [],
        )
        
        # 查找合适的智能体
        candidates = self._find_capable_agents(task_req)
        
        if not candidates:
            raise ValueError(f"没有智能体能够处理任务类型: {task_type.value}")
        
        # 选择最佳候选者
        best_candidate = self._select_best_candidate(candidates, task_req)
        
        # 检查能力边界冲突
        warnings = self._check_capability_conflicts(best_candidate, task_req, task_description)
        
        return TaskAssignment(
            task_id=f"task_{task_type.value}_{hash(task_description) % 10000}",
            task_requirement=task_req,
            assigned_agent=best_candidate,
            confidence=self._calculate_confidence(best_candidate, task_req),
            reasoning=self._generate_assignment_reasoning(best_candidate, task_req),
            alternatives=[c for c in candidates if c != best_candidate],
            warnings=warnings
        )
    
    def _find_capable_agents(self, task_req: TaskRequirement) -> List[AgentCapability]:
        """查找有能力处理任务的智能体"""
        candidates = []
        
        for agent in self.agents.values():
            if not agent.is_active:
                continue
            
            # 检查任务类型支持
            if task_req.task_type not in agent.supported_tasks:
                continue
            
            # 检查复杂度限制
            complexity_order = {"simple": 1, "medium": 2, "complex": 3}
            if complexity_order.get(task_req.complexity_level, 2) > complexity_order.get(agent.max_complexity, 2):
                continue
            
            # 检查必需工具
            missing_tools = set(task_req.required_tools) - agent.available_tools
            if missing_tools:
                self.logger.warning(f"智能体 {agent.agent_id} 缺少必需工具: {missing_tools}")
                continue
            
            candidates.append(agent)
        
        return candidates
    
    def _select_best_candidate(self, candidates: List[AgentCapability], 
                             task_req: TaskRequirement) -> AgentCapability:
        """选择最佳候选智能体"""
        if len(candidates) == 1:
            return candidates[0]
        
        # 计算每个候选者的得分
        scores = []
        for candidate in candidates:
            score = 0
            
            # 工具匹配度 (40%)
            tool_match_ratio = len(set(task_req.required_tools) & candidate.available_tools) / max(len(task_req.required_tools), 1)
            score += tool_match_ratio * 40
            
            # 专业化匹配度 (30%)
            specialization_bonus = 0
            for spec in candidate.specializations:
                if any(keyword in task_req.task_type.value for keyword in spec.split("_")):
                    specialization_bonus += 10
            score += min(specialization_bonus, 30)
            
            # 复杂度适配性 (20%)
            complexity_order = {"simple": 1, "medium": 2, "complex": 3}
            complexity_fit = 20 - abs(complexity_order.get(task_req.complexity_level, 2) - 
                                     complexity_order.get(candidate.max_complexity, 2)) * 5
            score += max(complexity_fit, 0)
            
            # 工具丰富度 (10%)
            tool_richness = min(len(candidate.available_tools) / 10 * 10, 10)
            score += tool_richness
            
            scores.append((candidate, score))
        
        # 返回得分最高的候选者
        best = max(scores, key=lambda x: x[1])
        return best[0]
    
    def _check_capability_conflicts(self, agent: AgentCapability, task_req: TaskRequirement, 
                                  task_description: str) -> List[str]:
        """检查能力边界冲突"""
        warnings = []
        
        # 检查智能体限制
        for limitation in agent.limitations:
            if self._check_limitation_conflict(limitation, task_description, task_req):
                warnings.append(f"任务可能违反智能体限制: {limitation}")
        
        # 检查特定冲突场景
        if agent.agent_role == AgentRole.VERILOG_DESIGNER:
            if "测试台" in task_description or "testbench" in task_description.lower():
                warnings.append("设计智能体不应负责测试台生成，建议分配给代码审查智能体")
            
        if agent.agent_role == AgentRole.CODE_REVIEWER:
            if "设计新模块" in task_description or "create new module" in task_description.lower():
                warnings.append("代码审查智能体不应负责设计新模块，建议分配给设计智能体")
        
        return warnings
    
    def _check_limitation_conflict(self, limitation: str, task_description: str, 
                                 task_req: TaskRequirement) -> bool:
        """检查特定限制冲突"""
        limitation_keywords = {
            "不生成测试台": ["测试台", "testbench", "test bench"],
            "不执行仿真": ["仿真", "simulation", "simulate"],  
            "不设计新模块": ["设计", "create", "generate new"],
            "不修改设计文件": ["修改", "modify", "edit", "change"]
        }
        
        keywords = limitation_keywords.get(limitation, [])
        return any(keyword in task_description.lower() for keyword in keywords)
    
    def _calculate_confidence(self, agent: AgentCapability, task_req: TaskRequirement) -> float:
        """计算任务分配置信度"""
        confidence = 0.5  # 基础置信度
        
        # 工具匹配度提升置信度
        if set(task_req.required_tools).issubset(agent.available_tools):
            confidence += 0.3
        
        # 专业化匹配提升置信度
        if any(spec in task_req.task_type.value for spec in agent.specializations):
            confidence += 0.15
        
        # 复杂度匹配提升置信度
        complexity_order = {"simple": 1, "medium": 2, "complex": 3}
        if complexity_order.get(task_req.complexity_level, 2) <= complexity_order.get(agent.max_complexity, 2):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _generate_assignment_reasoning(self, agent: AgentCapability, task_req: TaskRequirement) -> str:
        """生成任务分配推理"""
        reasons = []
        
        reasons.append(f"智能体角色({agent.agent_role.value})支持任务类型({task_req.task_type.value})")
        
        tool_match = set(task_req.required_tools) & agent.available_tools
        if tool_match:
            reasons.append(f"具备必需工具: {', '.join(tool_match)}")
        
        if agent.specializations:
            reasons.append(f"专业领域: {', '.join(agent.specializations)}")
        
        return "; ".join(reasons)
    
    def validate_task_description(self, task_description: str) -> Dict[str, Any]:
        """验证任务描述，识别可能的冲突"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "suggestions": [],
            "detected_task_types": []
        }
        
        # 检测任务类型
        task_indicators = {
            TaskType.DESIGN: ["设计", "创建", "生成模块", "create", "design"],
            TaskType.VERIFICATION: ["验证", "测试台", "testbench", "verify"],
            TaskType.SIMULATION: ["仿真", "运行", "simulation", "simulate"],
            TaskType.TESTING: ["测试", "test", "check"]
        }
        
        detected_types = []
        for task_type, keywords in task_indicators.items():
            if any(keyword in task_description.lower() for keyword in keywords):
                detected_types.append(task_type)
        
        validation_result["detected_task_types"] = detected_types
        
        # 检查冲突的任务类型组合
        if TaskType.DESIGN in detected_types and TaskType.VERIFICATION in detected_types:
            validation_result["warnings"].append("任务描述同时包含设计和验证需求，建议分解为子任务")
            validation_result["suggestions"].append("将任务分解为：1) 设计模块，2) 生成测试台和验证")
        
        return validation_result
    
    def get_agent_summary(self) -> Dict[str, Any]:
        """获取智能体能力摘要"""
        summary = {
            "total_agents": len(self.agents),
            "active_agents": sum(1 for a in self.agents.values() if a.is_active),
            "agents_by_role": {},
            "task_coverage": {}
        }
        
        # 按角色统计
        for agent in self.agents.values():
            role = agent.agent_role.value
            if role not in summary["agents_by_role"]:
                summary["agents_by_role"][role] = []
            summary["agents_by_role"][role].append({
                "id": agent.agent_id,
                "active": agent.is_active,
                "supported_tasks": [t.value for t in agent.supported_tasks]
            })
        
        # 任务覆盖统计
        for task_type in TaskType:
            capable_agents = [a.agent_id for a in self.agents.values() 
                            if task_type in a.supported_tasks and a.is_active]
            summary["task_coverage"][task_type.value] = {
                "agent_count": len(capable_agents),
                "agents": capable_agents
            }
        
        return summary


# 全局实例
_capability_manager_instance = None

def get_capability_manager() -> AgentCapabilityManager:
    """获取能力管理器实例"""
    global _capability_manager_instance
    if _capability_manager_instance is None:
        _capability_manager_instance = AgentCapabilityManager()
    return _capability_manager_instance

def reset_capability_manager():
    """重置能力管理器实例"""
    global _capability_manager_instance
    _capability_manager_instance = None