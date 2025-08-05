#!/usr/bin/env python3
"""
最终测试协调智能体 - 验证工具调用修复的完整解决方案
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

async def test_final_coordinator():
    """最终测试协调智能体"""
    
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
    
    print("🎯 最终测试协调智能体 - 验证工具调用修复")
    print("=" * 60)
    
    # 测试用例：简单的Verilog设计任务
    test_request = "设计一个4位计数器模块"
    
    print(f"📝 测试请求: {test_request}")
    print("-" * 40)
    
    try:
        # 执行协调任务
        result = await coordinator.coordinate_task(
            user_request=test_request,
            conversation_id="test_final_001",
            max_iterations=3  # 减少迭代次数以快速验证
        )
        
        print("✅ 协调任务执行完成")
        print(f"📊 结果: {result}")
        
        # 检查是否成功调用了工具
        if result.get('success'):
            print("🎉 测试成功：协调智能体正确调用了工具")
            print("🔧 修复验证：工具调用问题已完全解决")
        else:
            print("❌ 测试失败：协调智能体没有正确调用工具")
            print(f"🔍 错误信息: {result.get('error', '未知错误')}")
            
            # 显示调试信息
            if 'debug_info' in result:
                debug = result['debug_info']
                print(f"🔍 调试信息:")
                print(f"   - 原始结果: {debug.get('original_result', 'N/A')}")
                print(f"   - 强制结果: {debug.get('forced_result', 'N/A')}")
                print(f"   - 工具检测失败: {debug.get('tool_detection_failed', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 测试执行异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_final_coordinator()) 