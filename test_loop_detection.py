#!/usr/bin/env python3
"""
测试循环检测机制
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
        super().__init__(agent_id=agent_id, role="verilog_designer")
    
    async def _call_llm_for_function_calling(self, conversation):
        """模拟LLM调用"""
        return "测试响应"
    
    def get_capabilities(self):
        return {AgentCapability.CODE_REVIEW}
    
    def get_specialty_description(self):
        return "测试智能体"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        return {"success": True}


def test_loop_detection():
    """测试循环检测功能"""
    print("🧪 测试循环检测机制")
    print("=" * 50)
    
    agent = TestAgent("test_agent")
    
    # 模拟工具调用历史
    test_cases = [
        {
            "name": "正常执行",
            "tool_calls": [
                {"tool_name": "generate_verilog_code", "success": True},
                {"tool_name": "write_file", "success": True},
                {"tool_name": "analyze_code_quality", "success": True}
            ],
            "expected_loop": False
        },
        {
            "name": "检测到循环模式1",
            "tool_calls": [
                {"tool_name": "generate_verilog_code", "success": True},
                {"tool_name": "write_file", "success": True},
                {"tool_name": "analyze_code_quality", "success": True},
                {"tool_name": "write_file", "success": True},
                {"tool_name": "analyze_code_quality", "success": True},
                {"tool_name": "write_file", "success": True},
                {"tool_name": "analyze_code_quality", "success": True}
            ],
            "expected_loop": True
        },
        {
            "name": "检测到循环模式2",
            "tool_calls": [
                {"tool_name": "generate_verilog_code", "success": True},
                {"tool_name": "write_file", "success": True},
                {"tool_name": "analyze_code_quality", "success": True},
                {"tool_name": "generate_verilog_code", "success": True},
                {"tool_name": "write_file", "success": True},
                {"tool_name": "analyze_code_quality", "success": True}
            ],
            "expected_loop": True
        },
        {
            "name": "检测到重复操作",
            "tool_calls": [
                {"tool_name": "write_file", "success": True},
                {"tool_name": "write_file", "success": True},
                {"tool_name": "write_file", "success": True},
                {"tool_name": "write_file", "success": True}
            ],
            "expected_loop": True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        print(f"工具调用序列: {' -> '.join([call['tool_name'] for call in test_case['tool_calls']])}")
        
        # 模拟对话历史
        agent.conversation_history = []
        for call in test_case['tool_calls']:
            agent.conversation_history.append({
                "role": "user",
                "content": f"工具执行结果详细报告\n### ✅ 工具 1: {call['tool_name']} - 执行成功"
            })
        
        # 测试循环检测
        result = agent._validate_required_tool_calls()
        
        print(f"检测结果: {result['needs_continuation']}")
        print(f"原因: {result['reason']}")
        
        # 验证结果
        if result['needs_continuation'] == test_case['expected_loop']:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
            print(f"期望: {test_case['expected_loop']}, 实际: {result['needs_continuation']}")


def test_repetitive_detection():
    """测试重复操作检测"""
    print("\n🧪 测试重复操作检测")
    print("=" * 50)
    
    agent = TestAgent("test_agent")
    
    # 测试重复操作检测
    tool_calls = [
        {"tool_name": "write_file", "success": True},
        {"tool_name": "write_file", "success": True},
        {"tool_name": "write_file", "success": True},
        {"tool_name": "write_file", "success": True}
    ]
    
    result = agent._detect_repetitive_operations(tool_calls)
    print(f"重复操作检测结果: {result}")
    
    # 测试交替重复
    tool_calls_alt = [
        {"tool_name": "write_file", "success": True},
        {"tool_name": "analyze_code_quality", "success": True},
        {"tool_name": "write_file", "success": True},
        {"tool_name": "analyze_code_quality", "success": True}
    ]
    
    result_alt = agent._detect_repetitive_operations(tool_calls_alt)
    print(f"交替重复检测结果: {result_alt}")


if __name__ == "__main__":
    test_loop_detection()
    test_repetitive_detection()
    print("\n🎉 循环检测机制测试完成") 