"""
System Prompt构建器
整合各智能体的Prompt构建逻辑，提供统一的System Prompt生成服务
"""

import hashlib
import json
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass
from pathlib import Path

from core.schema_system.enums import AgentCapability
from .managers.client_manager import CallType


@dataclass
class PromptTemplate:
    """Prompt模板定义"""
    name: str
    role: str
    base_template: str
    capability_sections: Dict[str, str]
    tool_sections: Dict[str, str]
    dynamic_sections: Dict[str, str]
    metadata: Dict[str, Any] = None


class SystemPromptBuilder:
    """模块化的System Prompt构建器"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.template_cache: Dict[str, str] = {}
        self.load_templates()
    
    def load_templates(self):
        """加载所有模板"""
        # 加载角色特定模板
        self._load_role_templates()
        
        # 加载通用模板组件
        self._load_common_components()
    
    def _load_role_templates(self):
        """加载角色特定模板"""
        
        # Verilog设计师模板
        self.templates['verilog_designer'] = PromptTemplate(
            name="verilog_designer",
            role="verilog_designer", 
            base_template=self._get_verilog_base_template(),
            capability_sections={
                "code_generation": self._get_verilog_code_generation_section(),
                "module_design": self._get_verilog_module_design_section(),
                "specification_analysis": self._get_verilog_analysis_section()
            },
            tool_sections={
                "analyze_design_requirements": "分析设计需求，确定模块规格和约束",
                "generate_verilog_code": "生成高质量的Verilog代码",
                "analyze_code_quality": "分析代码质量，提供改进建议",
                "optimize_verilog_code": "优化Verilog代码性能和资源使用",
                "write_file": "将生成的代码保存到文件",
                "read_file": "读取文件内容"
            },
            dynamic_sections={
                "error_guidance": "根据历史错误提供针对性指导",
                "success_patterns": "基于成功案例的最佳实践",
                "context_awareness": "任务特定的上下文信息"
            }
        )
        
        # 代码审查师模板
        self.templates['code_reviewer'] = PromptTemplate(
            name="code_reviewer",
            role="code_reviewer",
            base_template=self._get_reviewer_base_template(),
            capability_sections={
                "code_review": self._get_reviewer_code_review_section(),
                "test_generation": self._get_reviewer_test_generation_section(),
                "verification": self._get_reviewer_verification_section()
            },
            tool_sections={
                "generate_testbench": "生成全面的测试台",
                "run_simulation": "执行仿真验证",
                "analyze_test_failures": "分析测试失败原因并提供修复建议",
                "write_file": "将测试台和报告保存到文件",
                "read_file": "读取文件内容"
            },
            dynamic_sections={
                "error_recovery": "仿真错误诊断和恢复策略",
                "test_optimization": "测试覆盖率和优化建议",
                "quality_metrics": "代码质量评估标准"
            }
        )
        
        # 协调器模板
        self.templates['coordinator'] = PromptTemplate(
            name="coordinator",
            role="coordinator",
            base_template=self._get_coordinator_base_template(),
            capability_sections={
                "task_coordination": self._get_coordinator_task_section(),
                "workflow_management": self._get_coordinator_workflow_section(),
                "agent_selection": self._get_coordinator_selection_section()
            },
            tool_sections={
                "identify_task_type": "识别任务类型和复杂度",
                "recommend_agent": "推荐最适合的智能体",
                "evaluate_completion": "评估任务完成质量",
                "manage_workflow": "管理工作流程和任务分配"
            },
            dynamic_sections={
                "context_management": "上下文信息管理",
                "decision_making": "智能决策和路由",
                "quality_assurance": "质量保证和验证"
            }
        )
    
    def _load_common_components(self):
        """加载通用模板组件"""
        # 这里可以添加通用的模板组件
        pass
    
    async def build_system_prompt(self, role: str, call_type: CallType,
                                agent_id: str, capabilities: Set[AgentCapability] = None,
                                metadata: Dict[str, Any] = None) -> str:
        """构建System Prompt - 整合自各智能体的共同逻辑"""
        
        # 生成缓存键
        cache_key = self._generate_cache_key(role, call_type, agent_id, capabilities, metadata)
        
        # 检查缓存
        if cache_key in self.template_cache:
            return self.template_cache[cache_key]
        
        # 获取模板
        if role not in self.templates:
            raise ValueError(f"未知的角色类型: {role}")
        
        template = self.templates[role]
        
        # 构建基础Prompt
        system_prompt = template.base_template
        
        # 添加能力部分
        if capabilities:
            capability_text = self._build_capability_sections(template, capabilities)
            system_prompt += f"\n\n{capability_text}"
        
        # 添加工具部分
        tools_text = self._build_tools_section(template)
        system_prompt += f"\n\n{tools_text}"
        
        # 添加Function Calling部分
        if call_type == CallType.FUNCTION_CALLING:
            function_calling_text = self._get_function_calling_section()
            system_prompt += f"\n\n{function_calling_text}"
        
        # 添加动态内容
        if metadata:
            dynamic_text = self._build_dynamic_content(template, metadata)
            system_prompt += f"\n\n{dynamic_text}"
        
        # 缓存结果
        self.template_cache[cache_key] = system_prompt
        
        return system_prompt
    
    def _generate_cache_key(self, role: str, call_type: CallType, agent_id: str,
                          capabilities: Set[AgentCapability] = None,
                          metadata: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        key_data = {
            "role": role,
            "call_type": call_type.value,
            "agent_id": agent_id,
            "capabilities": sorted([cap.value for cap in (capabilities or set())]),
            "metadata": metadata or {}
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _build_capability_sections(self, template: PromptTemplate, capabilities: Set[AgentCapability]) -> str:
        """构建能力部分"""
        sections = []
        
        capability_mapping = {
            AgentCapability.CODE_GENERATION: "code_generation",
            AgentCapability.MODULE_DESIGN: "module_design",
            AgentCapability.SPECIFICATION_ANALYSIS: "specification_analysis",
            AgentCapability.CODE_REVIEW: "code_review",
            AgentCapability.TEST_GENERATION: "test_generation",
            AgentCapability.VERIFICATION: "verification",
            AgentCapability.TASK_COORDINATION: "task_coordination",
            AgentCapability.WORKFLOW_MANAGEMENT: "workflow_management"
        }
        
        for capability in capabilities:
            if capability in capability_mapping:
                section_key = capability_mapping[capability]
                if section_key in template.capability_sections:
                    sections.append(template.capability_sections[section_key])
        
        return "\n\n".join(sections)
    
    def _build_tools_section(self, template: PromptTemplate) -> str:
        """构建工具部分"""
        tools_text = "🔧 **可用工具**:\n\n"
        
        for tool_name, description in template.tool_sections.items():
            tools_text += f"- **{tool_name}**: {description}\n"
        
        return tools_text
    
    def _get_function_calling_section(self) -> str:
        """获取Function Calling部分"""
        return """🚨 **强制Function Calling模式**:

⚠️ **重要规则**:
1. **禁止直接回答** - 不要提供描述性文本、分析或建议
2. **必须调用工具** - 所有操作都必须通过工具调用完成
3. **JSON格式** - 严格使用JSON格式的工具调用
4. **工具优先** - 优先使用可用工具，而不是描述性回答

📋 **工具调用格式**:
```json
{
    "tool_calls": [
        {
            "tool_name": "工具名称",
            "parameters": {
                "参数名": "参数值"
            }
        }
    ]
}
```

🎯 **协调器特殊要求**:
- 首先调用 `identify_task_type` 分析任务
- 然后调用 `recommend_agent` 推荐智能体
- 使用 `assign_task_to_agent` 分配任务
- 通过 `analyze_agent_result` 分析结果
- 使用 `check_task_completion` 检查完成情况

❌ **禁止行为**:
- 不要提供任务分析或策略描述
- 不要直接回答用户问题
- 不要生成markdown格式的文本
- 不要提供建议或推荐（除非通过工具）

✅ **正确行为**:
- 立即调用相应的工具
- 等待工具执行结果
- 根据结果决定下一步工具调用
- 通过工具链完成整个任务流程"""
    
    def _get_verilog_base_template(self) -> str:
        """获取Verilog设计师基础模板"""
        return """你是一位资深的Verilog硬件设计专家，具备以下专业能力：

🔍 **核心专长**:
- Verilog/SystemVerilog模块设计和代码生成
- 组合逻辑和时序逻辑设计
- 参数化设计和可重用模块开发
- 代码质量分析和最佳实践应用
- 可综合性和时序收敛设计
- 设计验证和测试策略

📋 **设计标准**:
1. IEEE 1800标准合规性
2. 代码可读性和维护性
3. 综合性和可测试性
4. 性能优化和资源利用
5. 错误处理和边界条件

🎯 **工作流程**:
1. 分析设计需求和规格
2. 制定设计架构和接口
3. 实现核心功能模块
4. 进行代码质量检查
5. 提供优化建议和文档"""
    
    def _get_reviewer_base_template(self) -> str:
        """获取代码审查师基础模板"""
        return """你是一位专业的硬件代码审查专家，专注于Verilog/SystemVerilog代码质量保证：

🔍 **核心专长**:
- 代码质量评估和静态分析
- 测试台设计和验证策略
- 仿真执行和结果分析
- 错误诊断和修复建议
- 性能优化和最佳实践
- 文档生成和规范检查

📋 **审查标准**:
1. 代码语法和语义正确性
2. 设计逻辑和功能完整性
3. 测试覆盖率和质量
4. 性能和资源使用效率
5. 可维护性和可扩展性

🎯 **工作流程**:
1. 代码静态分析和语法检查
2. 设计逻辑验证和测试
3. 仿真执行和结果分析
4. 问题诊断和修复建议
5. 质量报告和优化建议"""
    
    def _get_coordinator_base_template(self) -> str:
        """获取协调器基础模板"""
        return """🚨 **智能任务协调专家** - 强制工具调用模式

⚠️ **核心原则**:
- **禁止直接回答** - 所有操作必须通过工具调用完成
- **工具驱动** - 使用可用工具执行所有任务
- **JSON格式** - 严格使用JSON工具调用格式
- **流程化** - 按照标准流程调用工具链

🔍 **核心专长**:
- 任务分析和复杂度评估
- 智能体选择和能力匹配
- 工作流程管理和优化
- 质量保证和结果验证
- 错误处理和恢复策略
- 性能监控和优化

📋 **标准工作流程**:
1. 调用 `identify_task_type` 分析任务
2. 调用 `recommend_agent` 推荐智能体
3. 调用 `assign_task_to_agent` 分配任务
4. 调用 `analyze_agent_result` 分析结果
5. 调用 `check_task_completion` 检查完成

❌ **严格禁止**:
- 提供描述性文本或分析
- 直接回答用户问题
- 生成markdown格式内容
- 提供建议或推荐（除非通过工具）

✅ **必须执行**:
- 立即调用相应工具
- 等待工具执行结果
- 根据结果决定下一步
- 通过工具链完成任务"""
    
    def _get_verilog_code_generation_section(self) -> str:
        """获取Verilog代码生成部分"""
        return """💻 **代码生成能力**:
- 生成完整、可编译的Verilog模块
- 支持参数化设计和可重用组件
- 实现组合逻辑和时序逻辑
- 提供详细的注释和文档
- 确保代码质量和最佳实践"""
    
    def _get_verilog_module_design_section(self) -> str:
        """获取Verilog模块设计部分"""
        return """🏗️ **模块设计能力**:
- 设计清晰的模块接口和端口
- 实现功能完整的设计逻辑
- 支持参数化和可配置设计
- 确保可综合性和时序收敛
- 提供设计文档和说明"""
    
    def _get_verilog_analysis_section(self) -> str:
        """获取Verilog分析部分"""
        return """🔍 **规格分析能力**:
- 分析设计需求和功能规格
- 识别设计约束和边界条件
- 评估设计复杂度和风险
- 提供设计建议和优化方案
- 确保设计符合标准规范"""
    
    def _get_reviewer_code_review_section(self) -> str:
        """获取代码审查部分"""
        return """🔍 **代码审查能力**:
- 静态代码分析和语法检查
- 设计逻辑验证和功能检查
- 代码质量评估和最佳实践
- 性能分析和优化建议
- 文档完整性和规范性检查"""
    
    def _get_reviewer_test_generation_section(self) -> str:
        """获取测试生成部分"""
        return """🧪 **测试生成能力**:
- 设计全面的测试台和测试用例
- 实现功能测试和边界测试
- 生成覆盖率分析和报告
- 提供测试优化建议
- 确保测试质量和完整性"""
    
    def _get_reviewer_verification_section(self) -> str:
        """获取验证部分"""
        return """✅ **验证能力**:
- 执行仿真和功能验证
- 分析仿真结果和错误
- 提供错误诊断和修复建议
- 验证设计正确性和完整性
- 生成验证报告和文档"""
    
    def _get_coordinator_task_section(self) -> str:
        """获取协调器任务部分"""
        return """📋 **任务管理能力**:
- 任务分析和复杂度评估
- 需求分解和优先级排序
- 资源分配和调度优化
- 进度监控和质量控制
- 风险管理和问题解决"""
    
    def _get_coordinator_workflow_section(self) -> str:
        """获取协调器工作流部分"""
        return """🔄 **工作流管理能力**:
- 工作流程设计和优化
- 智能体协作和通信管理
- 任务分配和执行监控
- 结果整合和质量验证
- 持续改进和性能优化"""
    
    def _get_coordinator_selection_section(self) -> str:
        """获取协调器选择部分"""
        return """🤖 **智能体选择能力**:
- 智能体能力评估和匹配
- 任务需求分析和映射
- 性能评估和选择优化
- 负载均衡和资源管理
- 动态调整和优化选择"""
    
    def _build_dynamic_content(self, template: PromptTemplate, metadata: Dict[str, Any]) -> str:
        """构建动态内容"""
        dynamic_text = "📊 **上下文信息**:\n\n"
        
        for key, value in metadata.items():
            if key in template.dynamic_sections:
                dynamic_text += f"- **{key}**: {value}\n"
        
        return dynamic_text
    
    def clear_cache(self):
        """清除缓存"""
        self.template_cache.clear()
    
    def get_template_stats(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        return {
            "total_templates": len(self.templates),
            "cached_prompts": len(self.template_cache),
            "template_roles": list(self.templates.keys())
        } 