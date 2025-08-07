"""
System Prompt模板引擎
支持角色特定的提示模板和动态组合
"""

import json
import os
import hashlib
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path

from ..managers.client_manager import CallType
from core.schema_system.enums import AgentCapability


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


class PromptTemplateEngine:
    """Prompt模板引擎"""
    
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
                "assign_task_to_agent": "将任务分配给合适的智能体",
                "analyze_agent_result": "分析智能体执行结果",
                "identify_task_type": "识别任务类型和复杂度"
            },
            dynamic_sections={
                "agent_performance": "基于历史表现的智能体选择",
                "task_optimization": "任务分解和执行优化",
                "quality_control": "结果质量控制和验证"
            }
        )
    
    def _load_common_components(self):
        """加载通用模板组件"""
        # 这里可以加载通用的模板组件
        pass
    
    async def build_system_prompt(self, role: str, call_type: CallType,
                                agent_id: str, capabilities: Set[AgentCapability] = None,
                                metadata: Dict[str, Any] = None) -> str:
        """构建System Prompt"""
        
        # 生成缓存键
        cache_key = self._generate_cache_key(role, call_type, agent_id, capabilities, metadata)
        
        # 检查缓存
        if cache_key in self.template_cache:
            return self.template_cache[cache_key]
        
        # 获取模板
        template = self.templates.get(role)
        if not template:
            raise ValueError(f"No template found for role: {role}")
        
        # 构建Prompt
        prompt_parts = []
        
        # 1. 基础模板
        prompt_parts.append(template.base_template)
        
        # 2. 能力相关部分
        if capabilities:
            for capability in capabilities:
                capability_name = capability.value
                if capability_name in template.capability_sections:
                    prompt_parts.append(template.capability_sections[capability_name])
        
        # 3. 工具相关部分
        prompt_parts.append(self._build_tools_section(template))
        
        # 4. 动态部分
        if metadata:
            dynamic_content = self._build_dynamic_content(template, metadata)
            if dynamic_content:
                prompt_parts.append(dynamic_content)
        
        # 5. 调用类型特定部分
        if call_type == CallType.FUNCTION_CALLING:
            prompt_parts.append(self._get_function_calling_section())
        
        # 组合所有部分
        full_prompt = "\n\n".join(filter(None, prompt_parts))
        
        # 缓存结果
        self.template_cache[cache_key] = full_prompt
        
        return full_prompt
    
    def _generate_cache_key(self, role: str, call_type: CallType, agent_id: str,
                          capabilities: Set[AgentCapability] = None,
                          metadata: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        key_components = [
            role,
            call_type.value,
            agent_id
        ]
        
        if capabilities:
            key_components.append(",".join(sorted(cap.value for cap in capabilities)))
        
        if metadata:
            # 只包含稳定的metadata部分，排除动态内容
            stable_metadata = {k: v for k, v in metadata.items() 
                             if k in ['task_type', 'complexity_level', 'priority']}
            if stable_metadata:
                key_components.append(json.dumps(stable_metadata, sort_keys=True))
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
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
3. 综合性和时序收敛
4. 参数化和可重用性
5. 最佳实践和设计模式
6. 安全性和可靠性

🎯 **任务执行原则**:
- 根据需求智能判断设计类型（组合/时序/混合）
- 自动检测和适配参数化位宽需求
- 生成高质量、可综合的Verilog代码
- 提供详细的代码注释和文档
- 支持多种编码风格和设计模式
- 确保代码符合行业标准"""
    
    def _get_reviewer_base_template(self) -> str:
        """获取代码审查师基础模板"""
        return """你是一位专业的Verilog代码审查和验证专家，具备以下核心能力：

🔍 **审查专长**:
- Verilog代码质量分析和评估
- 测试台(testbench)生成和优化
- 仿真验证和调试
- 错误诊断和修复建议
- 覆盖率分析和测试优化
- 代码规范和最佳实践检查

🧪 **验证能力**:
- 功能验证和时序分析
- 边界条件和异常情况测试
- 仿真环境搭建和优化
- 自动化测试流程设计
- 调试工具和方法应用
- 验证报告生成和分析

⚡ **专业工具**:
- iverilog编译和仿真
- 测试向量生成和分析
- 波形分析和调试
- 覆盖率统计和报告
- 性能基准测试
- 错误分类和修复策略"""
    
    def _get_coordinator_base_template(self) -> str:
        """获取协调器基础模板"""
        return """你是一位智能的多智能体协调专家，负责任务分配、工作流管理和质量控制：

🧠 **协调能力**:
- 智能任务分析和分解
- 基于能力的智能体选择
- 工作流优化和管理
- 质量控制和结果验证
- 错误恢复和重试策略
- 性能监控和优化

📊 **决策原则**:
- 基于任务类型选择最适合的智能体
- 考虑历史表现和当前负载
- 确保任务执行的高质量完成
- 提供详细的执行分析和建议
- 支持并行处理和依赖管理
- 实现智能错误恢复和重试"""
    
    def _build_tools_section(self, template: PromptTemplate) -> str:
        """构建工具部分"""
        tools_section = "\n🛠️ **可用工具**:\n"
        tools_section += "你必须使用JSON格式调用工具，格式如下：\n"
        tools_section += """```json
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
```\n"""
        
        tools_section += "### 可用工具列表:\n"
        for tool_name, tool_desc in template.tool_sections.items():
            tools_section += f"- **{tool_name}**: {tool_desc}\n"
        
        return tools_section
    
    def _get_function_calling_section(self) -> str:
        """获取Function Calling特定部分"""
        return """
🚨 **强制规则 - 必须使用工具调用**:
1. **禁止直接生成代码**: 绝对禁止在回复中直接生成Verilog代码
2. **必须调用工具**: 所有设计任务都必须通过工具调用完成
3. **必须写入文件**: 生成的代码必须使用 `write_file` 工具保存到文件
4. **JSON格式输出**: 当需要调用工具时回复必须是JSON格式的工具调用

**正确的工作流程**:
1. 分析需求 → 调用相应的分析工具
2. 生成/审查代码 → 调用生成/审查工具
3. **保存文件** → 调用 `write_file` 保存结果到指定目录
4. 质量检查 → 调用质量分析工具 (可选)
5. **路径回传** → 在任务总结中列出所有生成文件的完整路径

立即开始工具调用，严格按照工具列表执行，不要直接生成任何代码！"""
    
    def _get_verilog_code_generation_section(self) -> str:
        """获取Verilog代码生成部分"""
        return """
🎯 **代码生成专长**:
- 组合逻辑设计：门级、数据流、行为级描述
- 时序逻辑设计：同步/异步复位、时钟域管理
- 参数化设计：可配置位宽、功能模块
- 状态机设计：Moore/Mealy状态机、状态编码优化
- 接口设计：标准总线接口、自定义协议
- 层次化设计：模块分解、接口定义"""
    
    def _get_verilog_module_design_section(self) -> str:
        """获取Verilog模块设计部分"""
        return """
🏗️ **模块设计能力**:
- 端口定义：输入/输出端口、参数化端口
- 内部结构：组合逻辑、时序逻辑、混合设计
- 时序约束：建立时间、保持时间、时钟周期
- 可综合性：RTL级描述、综合约束
- 可测试性：扫描链、BIST、边界扫描
- 可维护性：清晰结构、详细注释、命名规范"""
    
    def _get_verilog_analysis_section(self) -> str:
        """获取Verilog分析部分"""
        return """
🔍 **需求分析能力**:
- 功能需求：输入输出关系、算法实现
- 性能需求：时序要求、资源约束
- 接口需求：协议规范、信号定义
- 约束需求：时序约束、面积约束
- 测试需求：覆盖率要求、验证策略
- 文档需求：设计文档、用户手册"""
    
    def _get_reviewer_code_review_section(self) -> str:
        """获取代码审查部分"""
        return """
📋 **代码审查标准**:
- 语法检查：Verilog语法规范、关键字使用
- 风格检查：命名规范、代码格式、注释质量
- 逻辑检查：功能正确性、边界条件处理
- 性能检查：时序收敛、资源使用、功耗分析
- 可维护性：模块化程度、代码复用、文档完整性
- 可测试性：测试覆盖、调试便利性"""
    
    def _get_reviewer_test_generation_section(self) -> str:
        """获取测试生成部分"""
        return """
🧪 **测试台生成能力**:
- 功能测试：基本功能验证、边界条件测试
- 时序测试：时钟域测试、复位测试、时序约束验证
- 覆盖率测试：语句覆盖、分支覆盖、条件覆盖
- 性能测试：最大频率、资源使用、功耗测试
- 回归测试：自动化测试流程、持续集成
- 调试支持：波形输出、断言检查、错误报告"""
    
    def _get_reviewer_verification_section(self) -> str:
        """获取验证部分"""
        return """
✅ **验证方法学**:
- 仿真验证：功能仿真、时序仿真、门级仿真
- 形式验证：等价性检查、模型检查、属性验证
- 覆盖率分析：代码覆盖率、功能覆盖率、断言覆盖率
- 性能分析：时序分析、功耗分析、面积分析
- 错误诊断：错误定位、根因分析、修复建议
- 质量评估：代码质量评分、改进建议"""
    
    def _get_coordinator_task_section(self) -> str:
        """获取协调器任务部分"""
        return """
📋 **任务协调能力**:
- 任务分析：需求理解、复杂度评估、依赖关系识别
- 任务分解：子任务划分、优先级排序、资源分配
- 智能体选择：能力匹配、负载均衡、历史表现考虑
- 进度监控：执行状态跟踪、里程碑管理、风险预警
- 质量控制：结果验证、质量标准检查、改进建议
- 冲突解决：资源冲突、依赖冲突、优先级冲突"""
    
    def _get_coordinator_workflow_section(self) -> str:
        """获取协调器工作流部分"""
        return """
🔄 **工作流管理**:
- 流程设计：任务流程规划、并行处理优化
- 依赖管理：任务依赖关系、执行顺序控制
- 资源调度：智能体分配、负载均衡、资源优化
- 状态管理：任务状态跟踪、状态转换控制
- 异常处理：错误恢复、重试策略、降级处理
- 性能优化：执行效率提升、资源利用率优化"""
    
    def _get_coordinator_selection_section(self) -> str:
        """获取协调器选择部分"""
        return """
🎯 **智能体选择策略**:
- 能力匹配：任务需求与智能体能力匹配度评估
- 性能评估：历史成功率、响应时间、质量评分
- 负载均衡：当前负载状态、可用性检查
- 专业领域：特定领域专长、经验水平评估
- 协作能力：多智能体协作、信息传递效率
- 适应性：新任务适应能力、学习能力评估"""
    
    def _build_dynamic_content(self, template: PromptTemplate, metadata: Dict[str, Any]) -> str:
        """构建动态内容"""
        dynamic_parts = []
        
        for section_name, section_desc in template.dynamic_sections.items():
            if section_name in metadata:
                content = metadata[section_name]
                if content:
                    dynamic_parts.append(f"### {section_desc}:\n{content}")
        
        return "\n\n".join(dynamic_parts)
    
    def clear_cache(self):
        """清除模板缓存"""
        self.template_cache.clear()
    
    def get_template_stats(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        return {
            'total_templates': len(self.templates),
            'cached_prompts': len(self.template_cache),
            'template_roles': list(self.templates.keys())
        }