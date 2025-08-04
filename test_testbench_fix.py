#!/usr/bin/env python3
"""
测试修复后的测试台生成功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

async def test_testbench_generation():
    """测试测试台生成功能"""
    print("🧪 测试测试台生成功能...")
    
    # 创建配置和智能体
    config = FrameworkConfig.from_env()
    agent = EnhancedRealCodeReviewAgent(config)
    
    # 测试ALU模块
    alu_code = """module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果
    output        zero      // 零标志 (result == 0 时为1)
);

    // 根据操作码选择对应的操作
    always @(*) begin
        case (op)
            4'b0000: result = a + b;     // 加法
            4'b0001: result = a - b;     // 减法
            4'b0010: result = a & b;     // 逻辑与
            4'b0011: result = a | b;     // 逻辑或
            4'b0100: result = a ^ b;     // 异或
            4'b0101: result = a << b[4:0]; // 逻辑左移
            4'b0110: result = a >> b[4:0]; // 逻辑右移
            default: result = 32'h00000000; // 其他操作码
        endcase
    end
    
    // 零标志：当结果为0时输出1
    assign zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
    
endmodule"""
    
    # 测试不同的模块名情况
    test_cases = [
        ("alu_32bit", alu_code, "正确模块名"),
        ("wrong_name", alu_code, "错误模块名"),
        ("", alu_code, "空模块名")
    ]
    
    for module_name, code, description in test_cases:
        print(f"\n📋 测试用例: {description}")
        print(f"   提供模块名: {module_name}")
        
        result = await agent._tool_generate_testbench(
            module_name=module_name,
            module_code=code,
            test_scenarios=[
                {"name": "basic_test", "description": "基本功能测试"},
                {"name": "corner_test", "description": "边界条件测试"}
            ]
        )
        
        if result.get("success"):
            print(f"   ✅ 成功生成测试台")
            print(f"   实际模块名: {result.get('module_name')}")
            print(f"   测试台文件名: {result.get('testbench_filename')}")
        else:
            print(f"   ❌ 生成失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_testbench_generation())
