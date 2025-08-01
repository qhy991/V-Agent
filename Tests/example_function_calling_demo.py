#!/usr/bin/env python3
"""
Function Calling系统演示

Demonstration of the Function Calling System
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.real_code_reviewer import RealCodeReviewAgent
from config.config import FrameworkConfig

async def demo_function_calling():
    """演示Function Calling系统"""
    print("🚀 Function Calling系统演示")
    print("=" * 50)
    
    # 创建配置和智能体
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    print(f"✅ 智能体创建完成")
    print(f"🔧 可用工具: {list(agent.tool_registry.list_tools().keys())}")
    
    # 示例Verilog代码
    test_code = """
module demo_module(
    input wire clk,
    input wire rst_n,
    input wire [7:0] data_in,
    output reg [7:0] data_out
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        data_out <= 8'b0;
    end else begin
        data_out <= data_in;
    end
end

endmodule
"""
    
    print(f"\n📝 测试代码:")
    print(test_code)
    
    # 构建对话
    conversation = [
        {
            "role": "system",
            "content": agent._get_base_system_prompt()
        },
        {
            "role": "user",
            "content": f"请分析以下代码的质量并生成测试台：\n\n{test_code}"
        }
    ]
    
    print(f"\n🤖 发送请求到LLM...")
    
    # 执行对话
    response = await agent._call_llm(conversation)
    print(f"📄 LLM响应: {response[:200]}...")
    
    # 解析工具调用
    tool_calls = agent._parse_tool_calls(response)
    
    if tool_calls:
        print(f"\n🔧 检测到 {len(tool_calls)} 个工具调用:")
        
        for i, tool_call in enumerate(tool_calls, 1):
            print(f"  工具 {i}: {tool_call.tool_name}")
            print(f"  参数: {tool_call.parameters}")
            
            # 执行工具调用
            print(f"  🔄 执行中...")
            result = await agent._execute_tool_call(tool_call)
            
            if result.success:
                print(f"  ✅ 执行成功: {result.result.get('message', 'N/A')}")
                
                # 显示结果摘要
                if 'code_quality' in result.result:
                    quality = result.result['code_quality']
                    print(f"  📊 代码质量评分: {quality.get('overall_score', 'N/A')}")
                
                if 'testbench_code' in result.result:
                    testbench = result.result['testbench_code']
                    print(f"  📄 测试台代码长度: {len(testbench)} 字符")
            else:
                print(f"  ❌ 执行失败: {result.error}")
    else:
        print(f"\nℹ️ 未检测到工具调用，LLM直接提供了分析")
    
    print(f"\n🎉 演示完成!")

if __name__ == "__main__":
    asyncio.run(demo_function_calling()) 