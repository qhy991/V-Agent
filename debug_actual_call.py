#!/usr/bin/env python3
"""
直接测试调用
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

async def test_direct_call():
    """直接测试调用"""
    
    print("🧪 直接测试 execute_enhanced_task 调用")
    print("=" * 60)
    
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    task_message = TaskMessage(
        task_id="test_001",
        sender_id="test_sender", 
        receiver_id=agent.agent_id,
        message_type="design_request",
        content="测试简单8位加法器设计"
    )
    
    print(f"📝 智能体类型: {type(agent)}")
    print(f"📝 任务消息: {task_message}")
    
    try:
        print("\n🚀 开始调用 execute_enhanced_task...")
        
        result = await agent.execute_enhanced_task(
            enhanced_prompt="设计一个8位加法器",
            original_message=task_message,
            file_contents={}
        )
        
        print(f"✅ 调用成功!")
        print(f"📋 结果类型: {type(result)}")
        print(f"📋 结果键: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
    except Exception as e:
        print(f"❌ 调用失败: {type(e).__name__}: {e}")
        import traceback
        print("📋 完整错误:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_call())