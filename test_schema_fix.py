#!/usr/bin/env python3
"""
测试Schema修复后的工具调用能力
"""

import asyncio
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from core.base_agent import TaskMessage

async def test_schema_fixed_tools():
    """测试修复后的Schema工具调用"""
    
    print("🧪 测试Schema修复后的工具调用能力")
    print("=" * 60)
    
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    task_message = TaskMessage(
        task_id="test_schema_fix",
        sender_id="test_sender", 
        receiver_id=agent.agent_id,
        message_type="design_request",
        content="设计一个简单的8位加法器"
    )
    
    print(f"📝 智能体类型: {type(agent)}")
    print(f"📝 任务消息: {task_message.content}")
    
    try:
        print("\n🚀 开始执行测试...")
        
        result = await agent.execute_enhanced_task(
            enhanced_prompt="设计一个简单的8位加法器，支持基本的二进制加法运算",
            original_message=task_message,
            file_contents={}
        )
        
        if result.get("success", False):
            print(f"✅ 测试成功!")
            print(f"📋 结果类型: {type(result)}")
            print(f"📋 结果键: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            
            # 检查是否有工具调用
            tool_results = result.get("tool_results", [])
            if tool_results:
                print(f"🔧 工具调用数量: {len(tool_results)}")
                for i, tool_result in enumerate(tool_results, 1):
                    print(f"   {i}. 工具: {tool_result.get('tool_name', 'unknown')}, 成功: {tool_result.get('success', False)}")
            
            iterations = result.get("iterations", 1)
            print(f"🔄 总迭代次数: {iterations}")
            
        else:
            print(f"❌ 测试失败")
            error = result.get("error", "未知错误")
            print(f"📋 错误信息: {error}")
            
    except Exception as e:
        print(f"❌ 测试异常: {type(e).__name__}: {e}")
        import traceback
        print("📋 完整错误:")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔍 测试完成")

if __name__ == "__main__":
    asyncio.run(test_schema_fixed_tools())