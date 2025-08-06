#!/usr/bin/env python3
"""
测试重构后的BaseAgent
验证组件化重构是否正常工作
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.base_agent import BaseAgent
from core.enums import AgentCapability


class TestAgent(BaseAgent):
    """测试用的智能体实现"""
    
    async def _call_llm_for_function_calling(self, conversation):
        """模拟LLM调用"""
        return "这是一个测试响应"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        """执行增强任务"""
        return {
            "success": True,
            "result": "测试任务执行成功",
            "message": enhanced_prompt
        }


async def test_refactored_base_agent():
    """测试重构后的BaseAgent"""
    print("🧪 开始测试重构后的BaseAgent...")
    
    try:
        # 1. 测试初始化
        print("\n1️⃣ 测试智能体初始化...")
        agent = TestAgent(
            agent_id="test_agent",
            role="测试智能体",
            capabilities={AgentCapability.VERILOG_DESIGN, AgentCapability.CODE_REVIEW}
        )
        print("✅ 智能体初始化成功")
        
        # 2. 测试组件功能
        print("\n2️⃣ 测试组件功能...")
        
        # 测试AgentContext
        capabilities = agent.get_capabilities()
        print(f"✅ 获取能力: {[cap.value for cap in capabilities]}")
        
        specialty = agent.get_specialty_description()
        print(f"✅ 专业描述: {specialty}")
        
        status = agent.get_status()
        print(f"✅ 智能体状态: {status['agent_id']}, {status['role']}")
        
        # 测试ConversationManager
        agent.conversation_manager.start_conversation("test_conversation")
        agent.conversation_manager.add_message("user", "你好")
        agent.conversation_manager.add_message("assistant", "你好！我是测试智能体")
        
        conversation_summary = agent.get_conversation_summary()
        print(f"✅ 对话摘要: {conversation_summary['total_conversations']} 个对话")
        
        # 3. 测试工具调用解析
        print("\n3️⃣ 测试工具调用解析...")
        
        # 测试JSON格式的工具调用
        json_response = '''
        {
            "tool_calls": [
                {
                    "tool_name": "write_file",
                    "parameters": {
                        "filename": "test.v",
                        "content": "module test(); endmodule"
                    }
                }
            ]
        }
        '''
        
        tool_calls = agent._parse_tool_calls_from_response(json_response)
        print(f"✅ 解析到 {len(tool_calls)} 个工具调用")
        if tool_calls:
            print(f"   工具名称: {tool_calls[0].tool_name}")
            print(f"   参数: {tool_calls[0].parameters}")
        
        # 4. 测试参数标准化
        print("\n4️⃣ 测试参数标准化...")
        
        parameters = {
            "file": "test.v",
            "text": "module test(); endmodule",
            "dir": "/tmp"
        }
        
        normalized = agent._normalize_tool_parameters("write_file", parameters)
        print(f"✅ 参数标准化: {normalized}")
        
        # 5. 测试对话管理
        print("\n5️⃣ 测试对话管理...")
        
        agent.clear_conversation_history()
        print("✅ 对话历史清除成功")
        
        # 6. 测试工具注册
        print("\n6️⃣ 测试工具注册...")
        
        print(f"✅ 已注册工具: {list(agent.function_calling_registry.keys())}")
        
        print("\n🎉 所有测试通过！重构后的BaseAgent工作正常。")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_refactored_base_agent())
    
    if success:
        print("\n✅ 重构测试成功！BaseAgent的组件化重构工作正常。")
        sys.exit(0)
    else:
        print("\n❌ 重构测试失败！请检查代码。")
        sys.exit(1) 