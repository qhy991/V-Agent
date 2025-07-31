#!/usr/bin/env python3
"""
测试通用Function Calling系统

Test Universal Function Calling System
"""

import asyncio
import logging
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from config.config import FrameworkConfig

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_verilog_agent_function_calling():
    """测试Verilog设计智能体的Function Calling"""
    print("🔧 测试RealVerilogAgent Function Calling...")
    
    config = FrameworkConfig.from_env()
    agent = RealVerilogDesignAgent(config)
    
    test_request = """请设计一个8位计数器，要求：
1. 支持异步复位
2. 支持使能控制
3. 带有溢出标志输出
4. 分析代码质量并保存到文件"""
    
    try:
        response = await agent.process_with_function_calling(
            user_request=test_request,
            max_iterations=8
        )
        
        print("✅ Verilog Agent测试完成!")
        print("=" * 60)
        print("🤖 智能体响应:")
        print(response[:500] + "..." if len(response) > 500 else response)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Verilog Agent测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_code_reviewer_function_calling():
    """测试代码审查智能体的Function Calling"""
    print("\n🔍 测试RealCodeReviewAgent Function Calling...")
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    test_request = """请对以下简单计数器代码进行完整的功能验证：

```verilog
module simple_counter(
    input clk,
    input rst_n,
    input enable,
    output reg [7:0] count,
    output overflow
);

assign overflow = (count == 8'hFF);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        count <= 8'b0;
    else if (enable)
        count <= count + 1;
end

endmodule
```

要求：
1. 保存代码到文件
2. 生成测试台
3. 保存测试台到文件
4. 运行仿真验证
5. 分析测试结果
"""
    
    try:
        response = await agent.process_with_function_calling(
            user_request=test_request,
            max_iterations=10
        )
        
        print("✅ Code Reviewer测试完成!")
        print("=" * 60)
        print("🤖 智能体响应:")
        print(response[:500] + "..." if len(response) > 500 else response)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Code Reviewer测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_tool_failure_retry():
    """测试工具失败重试机制"""
    print("\n🔄 测试工具失败重试机制...")
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 测试不存在的文件读取（应该失败并重试）
    test_request = """请读取文件 "non_existent_file.v" 的内容"""
    
    try:
        response = await agent.process_with_function_calling(
            user_request=test_request,
            max_iterations=3
        )
        
        print("✅ 失败重试测试完成!")
        print("=" * 60)
        print("🤖 智能体响应:")
        print(response[:500] + "..." if len(response) > 500 else response)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 失败重试测试失败: {str(e)}")

async def main():
    """主测试函数"""
    print("🚀 开始通用Function Calling系统测试...")
    
    # 测试Verilog设计智能体
    await test_verilog_agent_function_calling()
    
    # 测试代码审查智能体
    await test_code_reviewer_function_calling()
    
    # 测试失败重试机制
    await test_tool_failure_retry()
    
    print("\n🎉 所有测试完成!")

if __name__ == "__main__":
    asyncio.run(main())