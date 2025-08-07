#!/usr/bin/env python3
"""
直接测试_build_user_message方法
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.llm_communication.managers.client_manager import UnifiedLLMClientManager

async def test_build_user_message():
    """直接测试_build_user_message方法"""
    print("🔍 直接测试_build_user_message方法...")
    
    try:
        # 1. 加载配置
        print("📋 加载配置...")
        config = FrameworkConfig.from_env()
        print(f"✅ 配置加载成功")
        
        # 2. 创建UnifiedLLMClientManager
        print("\n🔧 创建UnifiedLLMClientManager...")
        llm_manager = UnifiedLLMClientManager(
            agent_id="test_coordinator",
            role="coordinator",
            config=config
        )
        print("✅ UnifiedLLMClientManager创建成功")
        
        # 3. 测试正常的对话
        print("\n💬 测试正常的对话...")
        conversation = [
            {
                "role": "user",
                "content": "请帮我设计一个4位加法器"
            }
        ]
        
        user_message = llm_manager._build_user_message(conversation)
        print(f"✅ 正常对话构建成功")
        print(f"📝 用户消息长度: {len(user_message)}")
        print(f"📝 用户消息内容: {user_message}")
        
        # 4. 测试包含None内容的对话
        print("\n⚠️ 测试包含None内容的对话...")
        conversation_with_none = [
            {
                "role": "user",
                "content": None
            }
        ]
        
        try:
            user_message_none = llm_manager._build_user_message(conversation_with_none)
            print(f"✅ 包含None的对话构建成功")
            print(f"📝 用户消息长度: {len(user_message_none)}")
            print(f"📝 用户消息内容: {user_message_none}")
        except Exception as e:
            print(f"❌ 包含None的对话构建失败: {str(e)}")
            return False
        
        # 5. 测试包含空内容的对话
        print("\n⚠️ 测试包含空内容的对话...")
        conversation_with_empty = [
            {
                "role": "user",
                "content": ""
            }
        ]
        
        try:
            user_message_empty = llm_manager._build_user_message(conversation_with_empty)
            print(f"✅ 包含空内容的对话构建成功")
            print(f"📝 用户消息长度: {len(user_message_empty)}")
            print(f"📝 用户消息内容: {user_message_empty}")
        except Exception as e:
            print(f"❌ 包含空内容的对话构建失败: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_build_user_message())
    sys.exit(0 if success else 1) 