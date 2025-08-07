#!/usr/bin/env python3
"""
直接测试LLM客户端
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient

async def test_llm_client():
    """直接测试LLM客户端"""
    print("🔍 直接测试LLM客户端...")
    
    try:
        # 1. 加载配置
        print("📋 加载配置...")
        config = FrameworkConfig.from_env()
        print(f"✅ 配置加载成功")
        print(f"🤖 Provider: {config.llm.provider}")
        print(f"🤖 Model: {config.llm.model_name}")
        print(f"🤖 API Key: {'已设置' if config.llm.api_key else '未设置'}")
        if config.llm.api_key:
            print(f"🤖 API Key长度: {len(config.llm.api_key)}")
            print(f"🤖 API Key前缀: {config.llm.api_key[:10]}...")
        print(f"🤖 API Base URL: {config.llm.api_base_url}")
        
        # 2. 创建LLM客户端
        print("\n🔧 创建LLM客户端...")
        llm_client = EnhancedLLMClient(config.llm)
        print("✅ LLM客户端创建成功")
        
        # 3. 测试简单请求
        print("\n🚀 测试简单请求...")
        test_prompt = "请简单介绍一下你自己，用一句话回答。"
        
        response = await llm_client.send_prompt(
            prompt=test_prompt,
            system_prompt="你是一个有用的AI助手。",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"✅ 请求成功!")
        print(f"📝 响应: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_client())
    sys.exit(0 if success else 1) 