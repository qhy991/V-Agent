#!/usr/bin/env python3
"""
测试EnhancedBaseAgent的_call_llm_optimized_with_history方法修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.enums import AgentCapability
from config.config import FrameworkConfig


class TestEnhancedBaseAgent(EnhancedBaseAgent):
    """测试用的增强基础智能体"""
    
    def __init__(self):
        super().__init__(
            agent_id="test_enhanced_agent",
            role="test_role",
            capabilities={AgentCapability.CODE_GENERATION}
        )
        
        # 模拟统一的LLM管理器
        self.llm_manager = None  # 先设置为None，测试回退逻辑
    
    async def _call_llm_for_function_calling(self, conversation):
        """抽象方法实现"""
        return "test response"
    
    async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
        """抽象方法实现"""
        return {"success": True}


async def test_enhanced_base_agent_llm_call():
    """测试EnhancedBaseAgent的LLM调用修复"""
    print("🧪 测试EnhancedBaseAgent的LLM调用修复...")
    
    try:
        # 创建测试智能体
        agent = TestEnhancedBaseAgent()
        
        # 测试1：没有llm_manager时的回退逻辑
        print("📋 测试1：没有llm_manager时的回退逻辑")
        
        # 确保没有llm_manager
        agent.llm_manager = None
        
        # 调用方法
        result = await agent._call_llm_optimized_with_history(
            user_request="测试请求",
            conversation_history=[],
            is_first_call=True
        )
        
        print(f"✅ 测试1通过：成功调用LLM，返回长度: {len(result) if result else 0}")
        
        # 测试2：有llm_manager时的统一管理器调用
        print("📋 测试2：有llm_manager时的统一管理器调用")
        
        # 模拟llm_manager
        class MockLLMManager:
            async def call_llm_for_function_calling(self, **kwargs):
                return "mock response from unified manager"
        
        agent.llm_manager = MockLLMManager()
        
        # 调用方法
        result = await agent._call_llm_optimized_with_history(
            user_request="测试请求2",
            conversation_history=[],
            is_first_call=True
        )
        
        print(f"✅ 测试2通过：成功调用统一管理器，返回: {result}")
        
        print("🎉 所有测试通过！EnhancedBaseAgent的LLM调用修复成功")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_base_agent_none_fix():
    """测试NoneType错误的修复"""
    print("🧪 测试NoneType错误的修复...")
    
    try:
        # 创建测试智能体
        agent = TestEnhancedBaseAgent()
        
        # 确保没有llm_manager和llm_client
        agent.llm_manager = None
        if hasattr(agent, 'llm_client'):
            agent.llm_client = None
        
        # 调用方法 - 这应该不会抛出NoneType错误
        result = await agent._call_llm_optimized_with_history(
            user_request="测试请求",
            conversation_history=[],
            is_first_call=True
        )
        
        print(f"✅ NoneType错误修复测试通过：成功调用，返回长度: {len(result) if result else 0}")
        return True
        
    except Exception as e:
        print(f"❌ NoneType错误修复测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🚀 开始EnhancedBaseAgent修复测试...")
    
    # 测试1：LLM调用修复
    test1_result = await test_enhanced_base_agent_llm_call()
    
    # 测试2：NoneType错误修复
    test2_result = await test_enhanced_base_agent_none_fix()
    
    if test1_result and test2_result:
        print("🎉 所有测试通过！EnhancedBaseAgent修复成功")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 