#!/usr/bin/env python3
"""
简单测试重构后的组件
只测试已分解的组件功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_components():
    """测试已分解的组件"""
    print("🧪 开始测试已分解的组件...")
    
    try:
        # 1. 测试AgentContext
        print("\n1️⃣ 测试AgentContext组件...")
        from core.context.agent_context import AgentContext
        from core.enums import AgentCapability
        
        context = AgentContext(
            agent_id="test_agent",
            role="测试智能体",
            capabilities={AgentCapability.VERILOG_DESIGN}
        )
        
        print(f"✅ AgentContext创建成功: {context.agent_id}")
        print(f"✅ 能力: {[cap.value for cap in context.get_capabilities()]}")
        print(f"✅ 专业描述: {context.get_specialty_description()}")
        
        # 2. 测试ConversationManager
        print("\n2️⃣ 测试ConversationManager组件...")
        from core.conversation.manager import ConversationManager
        
        manager = ConversationManager("test_agent")
        manager.start_conversation("test_conv")
        manager.add_message("user", "你好")
        manager.add_message("assistant", "你好！")
        
        history = manager.get_conversation_history()
        print(f"✅ ConversationManager创建成功: {len(history)} 条消息")
        
        summary = manager.get_conversation_summary()
        print(f"✅ 对话摘要: {summary['message_count']} 条消息")
        
        # 3. 测试ToolCallParser
        print("\n3️⃣ 测试ToolCallParser组件...")
        from core.function_calling.parser import ToolCallParser
        
        parser = ToolCallParser()
        
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
        
        tool_calls = parser.parse_tool_calls_from_response(json_response)
        print(f"✅ ToolCallParser创建成功: 解析到 {len(tool_calls)} 个工具调用")
        
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
        
        normalized = parser.normalize_tool_parameters("write_file", parameters)
        print(f"✅ 参数标准化: {normalized}")
        
        print("\n🎉 所有组件测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_components()
    
    if success:
        print("\n✅ 组件测试成功！重构的组件工作正常。")
        sys.exit(0)
    else:
        print("\n❌ 组件测试失败！请检查代码。")
        sys.exit(1) 