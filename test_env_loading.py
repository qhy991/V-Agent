#!/usr/bin/env python3
"""
测试环境变量加载
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig

def test_env_loading():
    """测试环境变量加载"""
    print("🔍 测试环境变量加载...")
    
    # 1. 检查.env文件是否存在
    env_file = Path(".env")
    print(f"📁 .env文件存在: {env_file.exists()}")
    
    if env_file.exists():
        print(f"📁 .env文件大小: {env_file.stat().st_size} bytes")
    
    # 2. 检查环境变量是否已设置
    api_key = os.getenv("CIRCUITPILOT_DASHSCOPE_API_KEY")
    print(f"🔑 环境变量 CIRCUITPILOT_DASHSCOPE_API_KEY: {'已设置' if api_key else '未设置'}")
    if api_key:
        print(f"🔑 API密钥长度: {len(api_key)}")
        print(f"🔑 API密钥前缀: {api_key[:10]}...")
    
    # 3. 尝试加载FrameworkConfig
    try:
        print("\n🔄 尝试加载FrameworkConfig...")
        config = FrameworkConfig.from_env()
        print("✅ FrameworkConfig加载成功")
        
        # 检查LLM配置
        print(f"🤖 LLM Provider: {config.llm.provider}")
        print(f"🤖 LLM Model: {config.llm.model_name}")
        print(f"🤖 LLM API Key: {'已设置' if config.llm.api_key else '未设置'}")
        if config.llm.api_key:
            print(f"🤖 LLM API Key长度: {len(config.llm.api_key)}")
            print(f"🤖 LLM API Key前缀: {config.llm.api_key[:10]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ FrameworkConfig加载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_env_loading()
    sys.exit(0 if success else 1) 