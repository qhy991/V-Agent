#!/usr/bin/env python3
"""
动态System Prompt生成器
"""

import json
from typing import Dict, Any, List, Set
from core.enums import AgentCapability

class DynamicSystemPromptGenerator:
    """动态生成System Prompt以确保与实际可用工具匹配"""
    
    def __init__(self):
        self.base_rules = """
# 角色
你是一个智能协调器，负责协调多个智能体完成复杂任务。

# 🚨 强制规则 (必须严格遵守)
1. **禁止直接回答**: 绝对禁止直接回答用户的任何问题或请求。
2. **必须调用工具**: 你的所有回复都必须是JSON格式的工具调用。
3. **禁止生成描述性文本**: 绝对禁止生成任何解释、分析、策略描述或其他文本内容。
4. **禁止生成markdown格式**: 绝对禁止使用 ###、---、** 等markdown格式。
5. **禁止生成表格**: 绝对禁止生成任何表格或列表。
6. **🚨 禁止直接调用智能体工具**: 绝对禁止直接调用智能体名称作为工具。
7. **🚨 必须使用正确的工具**: 只能调用下面列出的可用工具。

# 输出格式要求
你的回复必须是严格的JSON格式：
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
"""
    
    def generate_coordination_prompt(self, 
                                  available_tools: Dict[str, Any],
                                  registered_agents: Dict[str, Any]) -> str:
        """
        生成协调智能体的System Prompt
        
        Args:
            available_tools: 实际可用的工具列表
            registered_agents: 已注册的智能体信息
        
        Returns:
            完整的System Prompt
        """
        
        # 生成智能体信息部分
        agents_section = self._generate_agents_section(registered_agents)
        
        # 生成工具使用指南
        tools_guide = self._generate_tools_guide(available_tools)
        
        # 生成可用工具列表
        tools_list = self._generate_tools_list(available_tools)
        
        # 生成工作流程指南
        workflow_guide = self._generate_workflow_guide(available_tools)
        
        # 生成示例
        examples = self._generate_examples(available_tools)
        
        # 组合完整的System Prompt
        full_prompt = f"""{self.base_rules}

{agents_section}

{tools_guide}

{workflow_guide}

{examples}

{tools_list}

# 立即行动
收到用户请求后，立即分析并调用第一个合适的工具开始执行。
"""
        
        return full_prompt
    
    def _generate_agents_section(self, registered_agents: Dict[str, Any]) -> str:
        """生成智能体信息部分"""
        if not registered_agents:
            return "# 🤖 可用智能体\n暂无已注册的智能体。"
        
        agents_info = []
        for agent_id, agent_info in registered_agents.items():
            capabilities = ", ".join([cap.value if hasattr(cap, 'value') else str(cap) 
                                    for cap in agent_info.capabilities])
            agents_info.append(f"## {agent_id}")
            agents_info.append(f"**专业领域**: {agent_info.specialty}")
            agents_info.append(f"**核心能力**: {capabilities}")
            agents_info.append(f"**当前状态**: {agent_info.status.value}")
            agents_info.append("")
        
        return f"""# 🤖 可用智能体

{chr(10).join(agents_info)}"""
    
    def _generate_tools_guide(self, available_tools: Dict[str, Any]) -> str:
        """生成工具使用指南"""
        tool_names = list(available_tools.keys())
        
        guide = """# 🛠️ 工具使用指南

## 基本原则
1. **只使用可用工具**: 只能调用下面列出的工具
2. **正确的调用方式**: 使用assign_task_to_agent分配任务给智能体
3. **严格的JSON格式**: 所有工具调用必须是有效的JSON

## 工具调用流程"""
        
        if "identify_task_type" in tool_names:
            guide += "\n1. 首先调用 `identify_task_type` 分析任务类型"
        
        if "assign_task_to_agent" in tool_names:
            guide += "\n2. 使用 `assign_task_to_agent` 分配任务给合适的智能体"
        
        if "analyze_agent_result" in tool_names:
            guide += "\n3. 使用 `analyze_agent_result` 分析智能体执行结果"
        
        if "provide_final_answer" in tool_names:
            guide += "\n4. 最后使用 `provide_final_answer` 提供最终答案"
        
        return guide
    
    def _generate_workflow_guide(self, available_tools: Dict[str, Any]) -> str:
        """生成工作流程指南"""
        return """
# 🔄 标准工作流程

1. **任务分析阶段**
   - 理解用户需求
   - 识别任务类型和复杂度
   - 确定所需的智能体类型

2. **任务分配阶段**  
   - 选择最合适的智能体
   - 制定详细的任务描述
   - 设置合理的期望输出

3. **执行监控阶段**
   - 监控智能体执行进度
   - 分析执行结果质量
   - 识别可能的问题

4. **结果整合阶段**
   - 汇总所有执行结果
   - 验证任务完成度
   - 提供最终答案
"""
    
    def _generate_examples(self, available_tools: Dict[str, Any]) -> str:
        """生成使用示例"""
        examples = []
        
        if "identify_task_type" in available_tools:
            examples.append("""
## 示例1: 任务类型识别
```json
{
    "tool_calls": [
        {
            "tool_name": "identify_task_type",
            "parameters": {
                "user_request": "设计一个4位计数器模块"
            }
        }
    ]
}
```""")
        
        if "assign_task_to_agent" in available_tools:
            examples.append("""
## 示例2: 任务分配
```json
{
    "tool_calls": [
        {
            "tool_name": "assign_task_to_agent",
            "parameters": {
                "agent_id": "enhanced_real_verilog_agent",
                "task_description": "设计一个4位二进制计数器，包含时钟、复位和使能信号",
                "task_type": "design",
                "priority": "medium"
            }
        }
    ]
}
```""")
        
        return f"# 📝 使用示例{chr(10).join(examples)}" if examples else ""
    
    def _generate_tools_list(self, available_tools: Dict[str, Any]) -> str:
        """生成可用工具列表"""
        tools_json = json.dumps(list(available_tools.values()), indent=2, ensure_ascii=False)
        
        return f"""
# 🔧 可用工具列表

以下是所有可用的工具及其规范：

```json
{tools_json}
```

**重要提醒**: 只能调用上述列表中的工具，不能调用任何其他工具或智能体名称。
"""
    
    def validate_prompt_consistency(self, 
                                  prompt: str, 
                                  available_tools: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证System Prompt与可用工具的一致性
        
        Returns:
            验证结果报告
        """
        report = {
            "is_consistent": True,
            "issues": [],
            "warnings": [],
            "suggestions": []
        }
        
        # 检查提到的工具是否都存在
        mentioned_tools = self._extract_mentioned_tools(prompt)
        available_tool_names = set(available_tools.keys())
        
        for tool in mentioned_tools:
            if tool not in available_tool_names:
                report["is_consistent"] = False
                report["issues"].append(f"System Prompt提到了不存在的工具: {tool}")
        
        # 检查是否遗漏了重要工具
        important_tools = {"assign_task_to_agent", "identify_task_type", "provide_final_answer"}
        missing_important = important_tools - available_tool_names
        
        for tool in missing_important:
            report["warnings"].append(f"缺少重要工具: {tool}")
        
        # 生成改进建议
        if not report["is_consistent"]:
            report["suggestions"].append("重新生成System Prompt以匹配可用工具")
        
        if report["warnings"]:
            report["suggestions"].append("考虑添加缺失的重要工具")
        
        return report
    
    def _extract_mentioned_tools(self, prompt: str) -> Set[str]:
        """从System Prompt中提取提到的工具名称"""
        import re
        
        # 查找所有被反引号包围的工具名称
        tool_patterns = [
            r'`([a-zA-Z_][a-zA-Z0-9_]*)`',
            r'"tool_name":\s*"([^"]+)"',
            r'调用\s*`?([a-zA-Z_][a-zA-Z0-9_]*)`?',
            r'使用\s*`?([a-zA-Z_][a-zA-Z0-9_]*)`?'
        ]
        
        mentioned_tools = set()
        for pattern in tool_patterns:
            matches = re.findall(pattern, prompt)
            mentioned_tools.update(matches)
        
        # 过滤掉明显不是工具名的词汇
        common_words = {"工具", "智能体", "agent", "tool", "function"}
        mentioned_tools = {tool for tool in mentioned_tools 
                         if tool not in common_words and not tool.isnumeric()}
        
        return mentioned_tools


# 使用示例
def demonstrate_dynamic_prompt():
    """演示动态System Prompt生成"""
    generator = DynamicSystemPromptGenerator()
    
    # 模拟可用工具
    mock_tools = {
        "identify_task_type": {
            "name": "identify_task_type",
            "description": "识别任务类型",
            "schema": {"type": "object", "properties": {"user_request": {"type": "string"}}}
        },
        "assign_task_to_agent": {
            "name": "assign_task_to_agent", 
            "description": "分配任务给智能体",
            "schema": {"type": "object", "properties": {"agent_id": {"type": "string"}}}
        }
    }
    
    # 模拟注册的智能体
    mock_agents = {
        "enhanced_real_verilog_agent": type('MockAgent', (), {
            'specialty': 'Verilog HDL设计专家',
            'capabilities': [AgentCapability.CODE_GENERATION],
            'status': type('Status', (), {'value': 'idle'})()
        })()
    }
    
    # 生成System Prompt
    prompt = generator.generate_coordination_prompt(mock_tools, mock_agents)
    print("生成的System Prompt:")
    print("=" * 50)
    print(prompt)
    
    # 验证一致性
    validation = generator.validate_prompt_consistency(prompt, mock_tools)
    print("\n验证结果:")
    print("=" * 50)
    print(json.dumps(validation, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    demonstrate_dynamic_prompt()