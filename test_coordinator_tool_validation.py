#!/usr/bin/env python3
"""
测试协调智能体工具调用验证修复
验证recommend_agent之后必须调用assign_task_to_agent的逻辑
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored as EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

class MockAgent(EnhancedBaseAgent):
    """模拟智能体用于测试"""
    
    def __init__(self, agent_id: str, role: str = "mock"):
        super().__init__(agent_id=agent_id, role=role)
        self.mock_tool_calls = []
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """模拟LLM调用"""
        return "模拟LLM响应"
    
    async def execute_enhanced_task(self, enhanced_prompt: str,
                                  original_message, file_contents: Dict[str, Dict]) -> Dict[str, Any]:
        """模拟任务执行"""
        return {"status": "success", "result": "模拟任务结果"}

def create_test_conversation_history() -> List[Dict[str, Any]]:
    """创建测试用的对话历史"""
    return [
        {
            "role": "user",
            "content": "请设计一个名为counter的Verilog模块",
            "timestamp": time.time() - 100
        },
        {
            "role": "assistant", 
            "content": '```json\n{\n    "tool_name": "identify_task_type",\n    "parameters": {\n        "user_request": "设计一个名为counter的Verilog模块",\n        "context": {}\n    }\n}\n```',
            "timestamp": time.time() - 90
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n### ✅ 工具 1: identify_task_type - 执行成功",
            "timestamp": time.time() - 80
        },
        {
            "role": "assistant",
            "content": '```json\n{\n    "tool_name": "recommend_agent",\n    "parameters": {\n        "task_type": "design",\n        "task_description": "设计一个名为counter的Verilog模块",\n        "priority": "medium"\n    }\n}\n```',
            "timestamp": time.time() - 70
        },
        {
            "role": "user", 
            "content": "工具执行结果详细报告\n### ✅ 工具 2: recommend_agent - 执行成功",
            "timestamp": time.time() - 60
        }
    ]

async def test_coordinator_tool_validation():
    """测试协调智能体工具调用验证"""
    print("🧪 开始测试协调智能体工具调用验证...")
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent()
    
    # 注册模拟智能体
    verilog_agent = EnhancedRealVerilogAgent()
    review_agent = EnhancedRealCodeReviewAgent()
    
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(review_agent)
    
    # 设置测试对话历史
    coordinator.conversation_history = create_test_conversation_history()
    
    print(f"📋 设置对话历史: {len(coordinator.conversation_history)} 条消息")
    
    # 测试工具调用提取
    tool_calls = coordinator._extract_tool_calls_from_history()
    print(f"🔧 提取的工具调用: {[call['tool_name'] for call in tool_calls]}")
    
    # 测试工具调用验证
    validation_result = coordinator._validate_required_tool_calls()
    print(f"✅ 验证结果: {validation_result}")
    
    # 验证结果
    expected_tools = ["identify_task_type", "recommend_agent"]
    actual_tools = [call["tool_name"] for call in tool_calls]
    
    print(f"📊 期望工具: {expected_tools}")
    print(f"📊 实际工具: {actual_tools}")
    
    # 检查是否检测到缺少assign_task_to_agent
    if validation_result.get("needs_continuation", False):
        print("✅ 正确检测到缺少assign_task_to_agent工具调用")
        print(f"📝 原因: {validation_result.get('reason', '')}")
        print(f"💡 建议: {validation_result.get('suggested_actions', [])}")
    else:
        print("❌ 未能检测到缺少assign_task_to_agent工具调用")
        return False
    
    return True

async def test_complete_workflow():
    """测试完整的工作流程"""
    print("\n🧪 测试完整工作流程...")
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent()
    
    # 注册智能体
    verilog_agent = EnhancedRealVerilogAgent()
    review_agent = EnhancedRealCodeReviewAgent()
    
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(review_agent)
    
    # 创建完整的对话历史（包含assign_task_to_agent）
    complete_history = create_test_conversation_history() + [
        {
            "role": "assistant",
            "content": '```json\n{\n    "tool_name": "assign_task_to_agent",\n    "parameters": {\n        "agent_id": "enhanced_real_verilog_agent",\n        "task_description": "设计一个名为counter的Verilog模块",\n        "task_type": "design",\n        "priority": "medium"\n    }\n}\n```',
            "timestamp": time.time() - 50
        },
        {
            "role": "user",
            "content": "工具执行结果详细报告\n### ✅ 工具 3: assign_task_to_agent - 执行成功",
            "timestamp": time.time() - 40
        }
    ]
    
    coordinator.conversation_history = complete_history
    
    # 测试工具调用验证
    validation_result = coordinator._validate_required_tool_calls()
    print(f"✅ 完整流程验证结果: {validation_result}")
    
    # 验证结果
    if not validation_result.get("needs_continuation", True):
        print("✅ 完整工作流程验证通过")
        return True
    else:
        print("❌ 完整工作流程验证失败")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始协调智能体工具调用验证测试")
    print("=" * 60)
    
    # 测试1: 验证缺少assign_task_to_agent的检测
    test1_result = await test_coordinator_tool_validation()
    
    # 测试2: 验证完整工作流程
    test2_result = await test_complete_workflow()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"测试1 (缺少工具检测): {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"测试2 (完整流程验证): {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！工具调用验证修复成功！")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    asyncio.run(main()) 