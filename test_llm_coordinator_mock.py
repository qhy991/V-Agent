#!/usr/bin/env python3
"""
使用模拟LLM客户端的协调器测试
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import FrameworkConfig, LLMConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored as EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

class MockLLMClient:
    """模拟LLM客户端，用于测试"""
    
    def __init__(self, config):
        self.config = config
        self.logger = None
    
    async def send_prompt(self, prompt: str, system_prompt: str = None, 
                         temperature: float = None, max_tokens: int = None, 
                         json_mode: bool = False) -> str:
        """模拟LLM响应"""
        return "这是一个模拟的LLM响应，用于测试重构后的代码。"
    
    async def send_prompt_optimized(self, conversation_id: str, user_message: str,
                                  system_prompt: str = None, temperature: float = None,
                                  max_tokens: int = None, json_mode: bool = False,
                                  force_refresh_system: bool = False) -> str:
        """模拟优化的LLM响应"""
        return "这是一个模拟的优化LLM响应，用于测试重构后的代码。"

class MockEnhancedLLMClient:
    """模拟增强LLM客户端"""
    
    def __init__(self, config):
        self.config = config
        self.optimized_client = MockLLMClient(config)
    
    async def send_prompt(self, prompt: str, system_prompt: str = None, 
                         temperature: float = None, max_tokens: int = None, 
                         json_mode: bool = False) -> str:
        """模拟LLM响应"""
        return "这是一个模拟的LLM响应，用于测试重构后的代码。"
    
    async def send_prompt_optimized(self, conversation_id: str, user_message: str,
                                  system_prompt: str = None, temperature: float = None,
                                  max_tokens: int = None, json_mode: bool = False,
                                  force_refresh_system: bool = False) -> str:
        """模拟优化的LLM响应"""
        return "这是一个模拟的优化LLM响应，用于测试重构后的代码。"

async def test_coordinator_with_mock():
    """使用模拟LLM客户端测试协调器"""
    print("🧪 开始模拟LLM客户端测试...")
    
    try:
        # 创建配置
        llm_config = LLMConfig(
            provider="mock",
            model_name="mock-model",
            api_key="mock-key",
            api_base_url="http://mock.local"
        )
        config = FrameworkConfig(llm_config=llm_config)
        
        # 创建协调器
        coordinator = LLMCoordinatorAgent(config)
        
        # 替换LLM客户端为模拟客户端
        coordinator.llm_manager.llm_client = MockEnhancedLLMClient(config.llm)
        
        # 创建智能体
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_review_agent = EnhancedRealCodeReviewAgent(config)
        
        # 注册智能体
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_review_agent)
        
        print("✅ 智能体注册成功")
        
        # 测试协调任务
        user_request = "请设计一个简单的计数器模块"
        result = await coordinator.coordinate_task(
            user_request=user_request,
            max_iterations=2
        )
        
        print(f"✅ 协调任务完成: {result}")
        
        # 测试LLM调用
        conversation = [
            {"role": "user", "content": "请说'Hello, World!'"}
        ]
        
        response = await coordinator._call_llm_for_function_calling(conversation)
        print(f"✅ Function Calling响应: {response}")
        
        response_traditional = await coordinator._call_llm_traditional(conversation)
        print(f"✅ 传统LLM响应: {response_traditional}")
        
        print("✅ 模拟LLM客户端测试完成")
        
    except Exception as e:
        print(f"❌ 模拟LLM客户端测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_coordinator_with_mock()) 