#!/usr/bin/env python3
"""
专门测试任务执行功能
"""

import asyncio
import sys
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
from config.config import FrameworkConfig
from core.base_agent import TaskMessage

async def test_task_execution_only():
    """只测试任务执行功能"""
    print("🧪 专门测试任务执行功能...")
    
    try:
        # 创建配置和智能体
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 创建测试任务消息
        task_message = TaskMessage(
            task_id="test_task_001",
            content="请设计一个简单的2位计数器模块",
            sender_id="test_user",
            receiver_id="verilog_agent",
            message_type="task_request"
        )
        
        # 测试文件内容
        file_contents = {
            "counter.v": {
                "content": "module counter_2bit(input clk, input rst, output [1:0] count);\n  reg [1:0] count_reg;\n  always @(posedge clk or posedge rst) begin\n    if (rst) count_reg <= 2'b00;\n    else count_reg <= count_reg + 1;\n  end\n  assign count = count_reg;\nendmodule",
                "type": "verilog"
            }
        }
        
        # 执行任务
        print("🚀 开始执行任务...")
        result = await agent.execute_enhanced_task(
            enhanced_prompt="请分析并优化这个2位计数器模块",
            original_message=task_message,
            file_contents=file_contents
        )
        
        print("✅ 任务执行成功")
        print(f"📊 结果类型: {type(result)}")
        print(f"📋 结果内容: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 任务执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🚀 开始专门的任务执行测试...\n")
    
    success = await test_task_execution_only()
    
    print("\n============================================================")
    print("📋 任务执行测试结果总结:")
    print(f"   任务执行: {'✅ 通过' if success else '❌ 失败'}")
    print("============================================================")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 