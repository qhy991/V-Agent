#!/usr/bin/env python3
"""
测试Function Calling实现

Test Function Calling Implementation
"""

import asyncio
import logging
from agents.real_code_reviewer import RealCodeReviewAgent
from config.config import FrameworkConfig

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_function_calling():
    """测试Function Calling功能"""
    
    # 初始化配置和智能体
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 测试用的简单ALU代码
    test_request = """
请对以下32位ALU代码进行完整的功能验证，包括生成测试台和运行仿真：

```verilog
module alu_32bit(
    input [31:0] a,
    input [31:0] b, 
    input [3:0] op,
    output reg [31:0] result,
    output zero,
    output overflow
);

assign zero = (result == 32'b0);
assign overflow = 1'b0; // 简化实现

always @(*) begin
    case(op)
        4'b0000: result = a + b;    // ADD
        4'b0001: result = a - b;    // SUB
        4'b0010: result = a & b;    // AND
        4'b0011: result = a | b;    // OR
        4'b0100: result = a ^ b;    // XOR
        4'b0101: result = ~a;       // NOT
        default: result = 32'b0;
    endcase
end

endmodule
```

要求：
1. 先将代码保存到文件
2. 生成完整的测试台
3. 将测试台保存到文件  
4. 使用iverilog运行仿真测试
5. 分析测试结果
"""
    
    print("🚀 开始测试Function Calling...")
    print(f"📝 测试请求: {test_request[:100]}...")
    
    try:
        # 使用Process with Function Calling处理请求
        response = await agent.process_with_function_calling(
            user_request=test_request,
            max_iterations=10  # 允许多轮工具调用
        )
        
        print("✅ Function Calling测试完成!")
        print("=" * 60)
        print("🤖 智能体响应:")
        print(response)
        print("=" * 60)
        
        # 检查生成的文件
        import os
        output_dir = "./output"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"📁 生成的文件: {files}")
        
    except Exception as e:
        print(f"❌ Function Calling测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_function_calling())