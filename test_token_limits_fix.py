#!/usr/bin/env python3
"""
🧪 测试LLM Token限制修复效果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from llm_integration.enhanced_llm_client import EnhancedLLMClient

async def test_token_limits():
    """测试各组件的token限制"""
    print("🧪 测试LLM Token限制修复效果")
    print("=" * 50)
    
    # 1. 测试配置读取
    config = FrameworkConfig.from_env()
    print(f"📋 环境变量配置:")
    print(f"   CAF_LLM_MAX_TOKENS: {config.llm.max_tokens}")
    
    # 2. 测试LLM客户端
    llm_client = EnhancedLLMClient(config.llm)
    print(f"🤖 LLM客户端配置:")
    print(f"   默认max_tokens: {llm_client.config.max_tokens}")
    
    # 3. 测试协调器配置
    coordinator = CentralizedCoordinator(config)
    print(f"🎛️ 协调器配置:")
    print(f"   分析max_tokens: {config.coordinator.analysis_max_tokens}")
    print(f"   决策max_tokens: {config.coordinator.decision_max_tokens}")
    
    # 4. 测试Verilog智能体
    verilog_agent = RealVerilogDesignAgent(config)
    print(f"🔧 Verilog智能体已初始化")
    
    print("✅ 所有组件token限制测试完成")
    print("如果看到更高的token值(如4000+)，说明修复成功！")

if __name__ == "__main__":
    asyncio.run(test_token_limits())
