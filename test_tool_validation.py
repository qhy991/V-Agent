#!/usr/bin/env python3
"""
测试工具调用验证机制
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.base_agent import BaseAgent
from core.enums import AgentCapability, AgentStatus


class TestAgent(BaseAgent):
    """测试用的智能体类"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id=agent_id, role="test_agent")
    
    async def _call_llm_for_function_calling(self, conversation):
        """模拟LLM调用"""
        return "测试响应"
    
    def get_capabilities(self):
        return {AgentCapability.CODE_REVIEW}
    
    def get_specialty_description(self):
        return "测试智能体"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        return {"success": True}


async def test_tool_validation():
    """测试工具调用验证机制"""
    print("🧪 开始测试工具调用验证机制...")
    
    # 测试1: 代码审查智能体缺少必需工具调用
    print("\n📋 测试1: 代码审查智能体缺少必需工具调用")
    code_review_agent = TestAgent("enhanced_real_code_review_agent")
    
    # 模拟对话历史 - 只调用了generate_testbench，没有调用run_simulation
    code_review_agent.conversation_history = [
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 1: generate_testbench - 执行成功\n\n**执行结果**: 测试台生成成功",
            "timestamp": 1000
        }
    ]
    
    # 执行验证
    validation_result = code_review_agent._validate_required_tool_calls()
    print(f"验证结果: {validation_result}")
    
    expected_missing = "run_simulation"
    if validation_result["needs_continuation"] and expected_missing in validation_result["reason"]:
        print("✅ 测试1通过: 正确检测到缺少run_simulation工具调用")
    else:
        print("❌ 测试1失败: 未能正确检测到缺少的工具调用")
    
    # 测试2: 代码审查智能体工具调用顺序正确
    print("\n📋 测试2: 代码审查智能体工具调用顺序正确")
    code_review_agent.conversation_history = [
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 1: write_file - 执行成功\n\n**执行结果**: 文件写入成功",
            "timestamp": 1000
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 2: generate_testbench - 执行成功\n\n**执行结果**: 测试台生成成功",
            "timestamp": 2000
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 3: run_simulation - 执行成功\n\n**执行结果**: 仿真执行成功",
            "timestamp": 3000
        }
    ]
    
    validation_result = code_review_agent._validate_required_tool_calls()
    print(f"验证结果: {validation_result}")
    
    if not validation_result["needs_continuation"]:
        print("✅ 测试2通过: 正确验证了工具调用顺序")
    else:
        print("❌ 测试2失败: 错误地认为工具调用顺序不正确")
    
    # 测试3: 代码审查智能体工具调用顺序错误
    print("\n📋 测试3: 代码审查智能体工具调用顺序错误")
    code_review_agent.conversation_history = [
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 1: write_file - 执行成功\n\n**执行结果**: 文件写入成功",
            "timestamp": 1000
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 2: run_simulation - 执行成功\n\n**执行结果**: 仿真执行成功",
            "timestamp": 2000
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 3: generate_testbench - 执行成功\n\n**执行结果**: 测试台生成成功",
            "timestamp": 3000
        }
    ]
    
    validation_result = code_review_agent._validate_required_tool_calls()
    print(f"验证结果: {validation_result}")
    
    if validation_result["needs_continuation"] and "顺序不正确" in validation_result["reason"]:
        print("✅ 测试3通过: 正确检测到工具调用顺序错误")
    else:
        print("❌ 测试3失败: 未能检测到工具调用顺序错误")
    
    # 测试4: Verilog设计智能体缺少必需工具调用
    print("\n📋 测试4: Verilog设计智能体缺少必需工具调用")
    verilog_agent = TestAgent("enhanced_real_verilog_agent")
    
    # 模拟对话历史 - 只调用了write_file，没有调用generate_verilog_code
    verilog_agent.conversation_history = [
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 1: write_file - 执行成功\n\n**执行结果**: 文件写入成功",
            "timestamp": 1000
        }
    ]
    
    validation_result = verilog_agent._validate_required_tool_calls()
    print(f"验证结果: {validation_result}")
    
    expected_missing = "generate_verilog_code"
    if validation_result["needs_continuation"] and expected_missing in validation_result["reason"]:
        print("✅ 测试4通过: 正确检测到缺少generate_verilog_code工具调用")
    else:
        print("❌ 测试4失败: 未能正确检测到缺少的工具调用")
    
    # 测试5: 协调智能体缺少必需工具调用
    print("\n📋 测试5: 协调智能体缺少必需工具调用")
    coordinator_agent = TestAgent("llm_coordinator_agent")
    
    # 模拟对话历史 - 只调用了identify_task_type，没有调用其他必需工具
    coordinator_agent.conversation_history = [
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 1: identify_task_type - 执行成功\n\n**执行结果**: 任务类型识别成功",
            "timestamp": 1000
        }
    ]
    
    validation_result = coordinator_agent._validate_required_tool_calls()
    print(f"验证结果: {validation_result}")
    
    if validation_result["needs_continuation"] and ("recommend_agent" in validation_result["reason"] or "assign_task_to_agent" in validation_result["reason"]):
        print("✅ 测试5通过: 正确检测到缺少协调智能体的必需工具调用")
    else:
        print("❌ 测试5失败: 未能正确检测到缺少的工具调用")
    
    # 测试6: 工具调用失败的情况
    print("\n📋 测试6: 工具调用失败的情况")
    code_review_agent.conversation_history = [
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 1: write_file - 执行成功\n\n**执行结果**: 文件写入成功",
            "timestamp": 1000
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 2: generate_testbench - 执行成功\n\n**执行结果**: 测试台生成成功",
            "timestamp": 2000
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ❌ 工具 3: run_simulation - 执行失败\n\n**执行结果**: 仿真执行失败",
            "timestamp": 3000
        }
    ]
    
    validation_result = code_review_agent._validate_required_tool_calls()
    print(f"验证结果: {validation_result}")
    
    if validation_result["needs_continuation"] and "执行失败" in validation_result["reason"]:
        print("✅ 测试6通过: 正确检测到工具调用失败")
    else:
        print("❌ 测试6失败: 未能检测到工具调用失败")
    
    # 测试7: 验证工具调用依赖关系
    print("\n📋 测试7: 验证工具调用依赖关系")
    code_review_agent.conversation_history = [
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 1: write_file - 执行成功\n\n**执行结果**: 文件写入成功",
            "timestamp": 1000
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n\n### ✅ 工具 2: generate_testbench - 执行成功\n\n**执行结果**: 测试台生成成功",
            "timestamp": 2000
        }
    ]
    
    validation_result = code_review_agent._validate_required_tool_calls()
    print(f"验证结果: {validation_result}")
    
    # 检查是否检测到缺少run_simulation（因为generate_testbench被调用后，run_simulation是下一个必需的）
    if validation_result["needs_continuation"] and "run_simulation" in validation_result["reason"]:
        print("✅ 测试7通过: 正确检测到缺少下一个必需的工具调用")
    else:
        print("❌ 测试7失败: 未能检测到缺少下一个必需的工具调用")
    
    print("\n🎉 工具调用验证机制测试完成！")


if __name__ == "__main__":
    asyncio.run(test_tool_validation()) 