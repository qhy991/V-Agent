#!/usr/bin/env python3
"""
测试对话流程修复
"""

import asyncio
import json
from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_code_reviewer import RealCodeReviewAgent
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent


async def test_conversation_fix():
    """测试对话修复"""
    print("🧪 开始测试对话流程修复...")
    
    # 初始化配置
    config = FrameworkConfig.from_env()
    
    # 创建协调者
    coordinator = CentralizedCoordinator(config)
    
    # 注册智能体
    review_agent = RealCodeReviewAgent(config)
    design_agent = VerilogDesignAgent(config)
    test_agent = VerilogTestAgent(config)
    
    coordinator.register_agent(review_agent)
    coordinator.register_agent(design_agent)
    coordinator.register_agent(test_agent)
    
    # 测试任务
    test_task = "请审查以下Verilog代码并提供改进建议：\nmodule test_module(input clk, input [7:0] data, output reg [7:0] result);\n  always @(posedge clk) begin\n    result <= data + 1;\n  end\nendmodule"
    
    try:
        # 执行测试
        print("🚀 开始测试任务...")
        result = await coordinator.coordinate_task_execution(test_task)
        
        print(f"✅ 测试完成！")
        print(f"📊 总轮次: {result['total_iterations']}")
        print(f"⏱️ 持续时间: {result['duration']:.2f}秒")
        print(f"🎯 任务完成: {result['success']}")
        print(f"👤 最终智能体: {result['final_speaker']}")
        
        if result['file_references']:
            print(f"📁 生成文件: {len(result['file_references'])}个")
            for ref in result['file_references']:
                print(f"  - {ref.file_path} ({ref.file_type})")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_conversation_fix())