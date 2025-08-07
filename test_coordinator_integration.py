#!/usr/bin/env python3
"""
LLM协调器智能体集成测试
验证重构后的协调器智能体功能
"""

import asyncio
import sys
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig

async def test_coordinator_integration():
    """测试协调器智能体集成"""
    print("🧪 开始LLM协调器智能体集成测试...")
    
    try:
        # 创建配置
        config = FrameworkConfig.from_env()
        
        # 创建协调器智能体
        coordinator = LLMCoordinatorAgent(config)
        print("✅ 协调器智能体创建成功")
        
        # 创建其他智能体
        verilog_agent = EnhancedRealVerilogAgentRefactored(config)
        code_reviewer = EnhancedRealCodeReviewAgent(config)
        print("✅ 其他智能体创建成功")
        
        # 注册智能体
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_reviewer)
        print("✅ 智能体注册成功")
        
        # 测试系统提示词构建
        system_prompt = await coordinator._build_enhanced_system_prompt()
        print(f"✅ 系统提示词构建成功，长度: {len(system_prompt)}")
        
        # 测试LLM调用
        test_conversation = [
            {"role": "user", "content": "请设计一个简单的2位计数器模块"}
        ]
        
        # 测试Function Calling
        function_response = await coordinator._call_llm_for_function_calling(test_conversation)
        print(f"✅ Function Calling测试成功，响应长度: {len(function_response)}")
        
        # 测试传统调用
        traditional_response = await coordinator._call_llm_traditional(test_conversation)
        print(f"✅ 传统LLM调用测试成功，响应长度: {len(traditional_response)}")
        
        # 测试工具注册
        registered_tools = coordinator.get_registered_tools()
        print(f"✅ 工具注册成功，工具数量: {len(registered_tools)}")
        
        # 测试智能体注册
        registered_agents = coordinator.get_registered_agents()
        print(f"✅ 智能体注册成功，智能体数量: {len(registered_agents)}")
        
        print("🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🚀 开始LLM协调器智能体集成测试...\n")
    
    success = await test_coordinator_integration()
    
    print("\n📋 测试结果总结:")
    if success:
        print("✅ 所有测试通过！LLM协调器智能体重构成功")
    else:
        print("❌ 测试失败，需要进一步调试")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 