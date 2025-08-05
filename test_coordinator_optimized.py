#!/usr/bin/env python3
"""
测试优化后的协调智能体 - 验证工具调用修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging

async def test_optimized_coordinator():
    """测试优化后的协调智能体"""
    
    # 设置日志
    setup_enhanced_logging()
    
    # 加载配置
    config = FrameworkConfig.from_env()
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent(config)
    
    # 创建并注册其他智能体
    verilog_agent = EnhancedRealVerilogAgent(config)
    review_agent = EnhancedRealCodeReviewAgent(config)
    
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(review_agent)
    
    print("🔧 测试优化后的协调智能体")
    print("=" * 50)
    
    # 测试用例1：简单的Verilog设计任务
    test_request = "设计一个4位计数器模块"
    
    print(f"📝 测试请求: {test_request}")
    print("-" * 30)
    
    try:
        # 执行协调任务
        result = await coordinator.coordinate_task(
            user_request=test_request,
            conversation_id="test_optimized_001",
            max_iterations=5
        )
        
        print("✅ 协调任务执行完成")
        print(f"📊 结果: {result}")
        
        # 检查是否成功调用了工具
        if result.get('success'):
            print("🎉 测试成功：协调智能体正确调用了工具")
        else:
            print("❌ 测试失败：协调智能体没有正确调用工具")
            print(f"🔍 错误信息: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 测试执行异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimized_coordinator()) 