#!/usr/bin/env python3
"""
测试API密钥加载和LLM调用
"""

import asyncio
import os
import sys
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient

async def test_api_key_loading():
    """测试API密钥加载"""
    print("🔍 测试API密钥加载...")
    
    # 方法1: 直接检查环境变量
    print(f"📋 环境变量 CIRCUITPILOT_DASHSCOPE_API_KEY: {os.getenv('CIRCUITPILOT_DASHSCOPE_API_KEY', '未设置')}")
    
    # 方法2: 使用FrameworkConfig.from_env()
    try:
        config = FrameworkConfig.from_env()
        print(f"✅ 配置加载成功")
        print(f"📋 LLM提供商: {config.llm.provider}")
        print(f"📋 模型名称: {config.llm.model_name}")
        print(f"📋 API密钥: {config.llm.api_key[:10]}..." if config.llm.api_key else "❌ API密钥未设置")
        print(f"📋 API基础URL: {config.llm.api_base_url}")
        
        return config
        
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        return None

async def test_llm_call(config):
    """测试LLM调用"""
    if not config or not config.llm.api_key:
        print("❌ 无法测试LLM调用 - API密钥未设置")
        return False
    
    print("\n🧪 测试LLM调用...")
    
    try:
        # 创建LLM客户端
        llm_client = EnhancedLLMClient(config.llm)
        
        # 简单测试
        test_prompt = "请回复'Hello World'"
        print(f"📤 发送测试请求: {test_prompt}")
        
        response = await llm_client.send_prompt(test_prompt)
        print(f"📥 收到响应: {response}")
        
        await llm_client.close()
        return True
        
    except Exception as e:
        print(f"❌ LLM调用失败: {str(e)}")
        return False

async def main():
    """主函数"""
    print("🚀 开始API密钥和LLM调用测试")
    
    # 测试API密钥加载
    config = await test_api_key_loading()
    
    # 测试LLM调用
    if config:
        success = await test_llm_call(config)
        if success:
            print("\n✅ 所有测试通过！LLM调用正常工作")
        else:
            print("\n❌ LLM调用测试失败")
    else:
        print("\n❌ API密钥加载失败")

if __name__ == "__main__":
    asyncio.run(main()) 