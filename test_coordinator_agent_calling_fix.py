#!/usr/bin/env python3
"""
测试协调智能体的智能体调用方法修复
验证系统提示词是否正确教会了LLM如何调用智能体
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig
from core.enhanced_logging_config import setup_enhanced_logging

async def test_coordinator_agent_calling_fix():
    """测试协调智能体的智能体调用方法修复"""
    
    print("🧪 开始测试协调智能体的智能体调用方法修复")
    print("=" * 60)
    
    # 设置日志
    setup_enhanced_logging()
    
    # 加载配置
    config = FrameworkConfig.from_env()
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent(config)
    
    # 创建并注册其他智能体
    verilog_agent = EnhancedRealVerilogAgent(config)
    code_review_agent = EnhancedRealCodeReviewAgent(config)
    
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(code_review_agent)
    
    print("✅ 智能体注册完成")
    print(f"📋 已注册智能体: {list(coordinator.get_registered_agents().keys())}")
    
    # 测试任务
    test_request = "设计一个4位计数器模块"
    conversation_id = f"test_agent_calling_fix_{int(datetime.now().timestamp())}"
    
    print(f"\n🎯 测试任务: {test_request}")
    print(f"🆔 对话ID: {conversation_id}")
    print("-" * 60)
    
    try:
        # 执行协调任务
        result = await coordinator.coordinate_task(
            user_request=test_request,
            conversation_id=conversation_id,
            max_iterations=3  # 限制迭代次数以便观察
        )
        
        print("\n📊 协调结果:")
        print(f"✅ 成功: {result.get('success', False)}")
        print(f"📝 结果: {result.get('result', 'N/A')[:200]}...")
        print(f"⏱️  执行时间: {result.get('execution_time', 0):.2f}秒")
        
        # 检查是否有工具调用
        if 'tool_calls_executed' in result:
            print(f"🛠️  工具调用次数: {result['tool_calls_executed']}")
        
        # 检查是否有智能体参与
        if 'agents_involved' in result:
            print(f"🤖 参与的智能体: {result['agents_involved']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(test_coordinator_agent_calling_fix())
    
    if result:
        print("\n🎉 测试完成！")
        if result.get('success', False):
            print("✅ 协调智能体成功执行了任务")
        else:
            print("⚠️  协调智能体执行了任务但可能存在问题")
    else:
        print("\n❌ 测试失败") 