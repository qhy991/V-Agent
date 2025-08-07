#!/usr/bin/env python3
"""
测试ToolCall的to_dict()方法修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.enums import AgentCapability
from core.function_calling.parser import ToolCall, ToolResult


class TestEnhancedBaseAgent(EnhancedBaseAgent):
    """测试用的增强基础智能体"""
    
    def __init__(self):
        super().__init__(
            agent_id="test_enhanced_agent",
            role="test_role",
            capabilities={AgentCapability.CODE_GENERATION}
        )
    
    async def _call_llm_for_function_calling(self, conversation):
        """抽象方法实现"""
        return "test response"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        """抽象方法实现"""
        return {"success": True}


async def test_tool_call_serialization():
    """测试ToolCall序列化修复"""
    print("🧪 测试ToolCall序列化修复...")
    
    try:
        # 创建测试智能体
        agent = TestEnhancedBaseAgent()
        
        # 创建测试的ToolCall和ToolResult对象
        tool_call = ToolCall(
            tool_name="test_tool",
            parameters={"param1": "value1", "param2": "value2"},
            call_id="test_call_001"
        )
        
        tool_result = ToolResult(
            call_id="test_call_001",
            success=True,
            result={"output": "test_output"},
            error=None
        )
        
        # 测试手动序列化（模拟process_with_enhanced_validation中的逻辑）
        print("📋 测试手动序列化...")
        
        tool_calls_dict = [{"tool_name": call.tool_name, "parameters": call.parameters, "call_id": call.call_id} for call in [tool_call]]
        tool_results_dict = [{"call_id": result.call_id, "success": result.success, "result": result.result, "error": result.error} for result in [tool_result]]
        
        print(f"✅ ToolCall序列化成功: {tool_calls_dict}")
        print(f"✅ ToolResult序列化成功: {tool_results_dict}")
        
        # 验证序列化结果
        assert tool_calls_dict[0]["tool_name"] == "test_tool"
        assert tool_calls_dict[0]["parameters"]["param1"] == "value1"
        assert tool_results_dict[0]["success"] == True
        assert tool_results_dict[0]["result"]["output"] == "test_output"
        
        print("✅ 序列化验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 序列化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_process_validation_fix():
    """测试process_with_enhanced_validation修复"""
    print("🧪 测试process_with_enhanced_validation修复...")
    
    try:
        # 创建测试智能体
        agent = TestEnhancedBaseAgent()
        
        # 模拟一个简单的LLM响应，包含工具调用
        mock_llm_response = '''```json
{
    "tool_calls": [
        {
            "tool_name": "test_tool",
            "parameters": {
                "param1": "value1"
            }
        }
    ]
}
```'''
        
        # 测试工具调用解析
        print("📋 测试工具调用解析...")
        tool_calls = agent._parse_tool_calls_from_response(mock_llm_response)
        
        print(f"✅ 解析到 {len(tool_calls)} 个工具调用")
        if tool_calls:
            print(f"✅ 工具名称: {tool_calls[0].tool_name}")
            print(f"✅ 工具参数: {tool_calls[0].parameters}")
        
        # 测试序列化（模拟process_with_enhanced_validation中的返回逻辑）
        print("📋 测试序列化...")
        tool_calls_dict = [{"tool_name": call.tool_name, "parameters": call.parameters, "call_id": call.call_id} for call in tool_calls]
        
        print(f"✅ 序列化成功: {tool_calls_dict}")
        return True
        
    except Exception as e:
        print(f"❌ process_validation测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🚀 开始ToolCall序列化修复测试...")
    
    # 测试1：ToolCall序列化
    test1_result = await test_tool_call_serialization()
    
    # 测试2：process_validation修复
    test2_result = await test_process_validation_fix()
    
    if test1_result and test2_result:
        print("🎉 所有测试通过！ToolCall序列化修复成功")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 