#!/usr/bin/env python3
"""
测试协调智能体修复效果
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig

async def test_coordinator_fix():
    """测试协调智能体修复效果"""
    print("🧪 开始测试协调智能体修复效果...")
    
    # 初始化配置
    config = FrameworkConfig.from_env()
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent(config)
    
    # 创建并注册智能体
    verilog_agent = EnhancedRealVerilogAgentRefactored(config)
    review_agent = EnhancedRealCodeReviewAgent(config)
    
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(review_agent)
    
    # 测试任务
    test_request = "请设计一个名为 counter 的Verilog模块。基本要求：1. 生成完整、可编译的Verilog代码 2. 包含适当的端口定义和功能实现 3. 符合Verilog标准语法 4. 生成对应的测试台进行验证"
    
    print(f"📋 测试任务: {test_request}")
    print("=" * 80)
    
    try:
        # 执行协调任务
        result = await coordinator.coordinate_task(
            user_request=test_request,
            max_iterations=10
        )
        
        print("✅ 协调任务执行完成")
        print(f"📊 结果: {result}")
        
        # 检查结果
        if result.get("success", False):
            print("🎉 测试成功：任务正常完成")
        else:
            print(f"❌ 测试失败：{result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 测试异常：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_coordinator_fix()) 