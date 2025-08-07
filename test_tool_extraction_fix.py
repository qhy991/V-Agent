#!/usr/bin/env python3
"""
测试工具调用提取修复 - 验证从对话历史中正确提取工具调用
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.base_agent import BaseAgent
import logging
import time

class TestAgent(BaseAgent):
    """测试用的智能体类"""
    
    def __init__(self):
        super().__init__("test_agent", "llm_coordinator")
        self.conversation_history = []
    
    async def _call_llm_for_function_calling(self, conversation):
        return "test response"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        return {"success": True}

def test_tool_extraction():
    """测试工具调用提取功能"""
    print("🧪 测试工具调用提取修复...")
    
    # 创建测试智能体
    agent = TestAgent()
    
    # 模拟对话历史 - 包含LLM返回的工具调用
    agent.conversation_history = [
        {
            "role": "user",
            "content": "请设计一个计数器",
            "timestamp": time.time()
        },
        {
            "role": "assistant", 
            "content": '''```json
{
    "tool_name": "identify_task_type",
    "parameters": {
        "user_request": "设计一个计数器"
    }
}
```''',
            "timestamp": time.time()
        },
        {
            "role": "assistant",
            "content": '''```json
{
    "tool_name": "recommend_agent", 
    "parameters": {
        "task_type": "design",
        "task_description": "设计一个计数器"
    }
}
```''',
            "timestamp": time.time()
        },
        {
            "role": "assistant",
            "content": '''```json
{
    "tool_name": "assign_task_to_agent",
    "parameters": {
        "agent_id": "enhanced_real_verilog_agent",
        "task_description": "设计一个计数器"
    }
}
```''',
            "timestamp": time.time()
        }
    ]
    
    # 提取工具调用
    tool_calls = agent._extract_tool_calls_from_history()
    
    print(f"\n📋 提取到的工具调用数量: {len(tool_calls)}")
    for i, tool_call in enumerate(tool_calls):
        print(f"   工具调用 {i}: {tool_call['tool_name']}")
    
    # 验证是否包含所有必需的工具调用
    expected_tools = ["identify_task_type", "recommend_agent", "assign_task_to_agent"]
    extracted_tools = [call["tool_name"] for call in tool_calls]
    
    print(f"\n🔍 期望的工具调用: {expected_tools}")
    print(f"🔍 提取的工具调用: {extracted_tools}")
    
    # 验证工具调用验证
    validation_result = agent._validate_required_tool_calls()
    print(f"\n✅ 工具调用验证结果: {validation_result}")
    
    # 检查是否所有必需工具都被调用
    missing_tools = [tool for tool in expected_tools if tool not in extracted_tools]
    if missing_tools:
        print(f"❌ 缺少工具调用: {missing_tools}")
        return False
    else:
        print("✅ 所有必需的工具调用都已提取")
        return True

if __name__ == "__main__":
    success = test_tool_extraction()
    if success:
        print("\n🎉 测试通过！工具调用提取修复有效")
    else:
        print("\n❌ 测试失败！工具调用提取仍有问题") 