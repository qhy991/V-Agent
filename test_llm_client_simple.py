#!/usr/bin/env python3
"""
简单的LLM客户端测试
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient

async def test_llm_client():
    """测试LLM客户端的基本功能"""
    print("🧪 开始LLM客户端测试...")
    
    try:
        # 加载配置
        config = FrameworkConfig()
        print(f"✅ 配置加载成功: {config.llm.model_name}")
        
        # 创建客户端
        client = EnhancedLLMClient(config.llm)
        print(f"✅ 客户端创建成功: {config.llm.provider}")
        
        # 测试基本调用
        print("🔄 测试基本LLM调用...")
        response = await client.send_prompt(
            prompt="请说'Hello, World!'",
            system_prompt="你是一个简单的测试助手。",
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ LLM响应: {response}")
        print(f"📊 响应长度: {len(response) if response else 0}")
        
        # 测试优化调用
        print("🔄 测试优化LLM调用...")
        response_optimized = await client.send_prompt_optimized(
            conversation_id="test_conversation",
            user_message="请说'Hello, World!'",
            system_prompt="你是一个简单的测试助手。",
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ 优化LLM响应: {response_optimized}")
        print(f"📊 优化响应长度: {len(response_optimized) if response_optimized else 0}")
        
        # 获取统计信息
        stats = client.get_stats()
        print(f"📊 客户端统计: {stats}")
        
        print("✅ LLM客户端测试完成")
        
    except Exception as e:
        print(f"❌ LLM客户端测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_client()) 