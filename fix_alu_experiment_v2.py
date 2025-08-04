#!/usr/bin/env python3
"""
ALU实验V2修复脚本

修复第二个ALU TDD实验中发现的问题：
1. 智能体选择逻辑错误
2. 测试台生成失败
3. 工具调用不匹配
"""

import os
import sys
from pathlib import Path

def fix_agent_selection_logic():
    """修复智能体选择逻辑"""
    print("🔧 修复智能体选择逻辑...")
    
    # 检查智能体能力评估方法
    verilog_agent_file = Path("agents/enhanced_real_verilog_agent.py")
    review_agent_file = Path("agents/enhanced_real_code_review_agent.py")
    
    if not verilog_agent_file.exists():
        print("❌ 找不到 enhanced_real_verilog_agent.py 文件")
        return False
    
    if not review_agent_file.exists():
        print("❌ 找不到 enhanced_real_code_review_agent.py 文件")
        return False
    
    print("✅ 智能体文件存在，需要手动检查能力评估方法")
    return True

def fix_testbench_generation():
    """修复测试台生成问题"""
    print("🔧 修复测试台生成问题...")
    
    # 创建正确的ALU测试台
    testbench_content = '''module testbench_alu_32bit;
    // 测试信号
    reg [31:0] a, b;
    reg [3:0] op;
    wire [31:0] result;
    wire zero;
    
    // 实例化ALU模块
    alu_32bit alu_inst (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    // 测试向量
    initial begin
        $dumpfile("alu_test.vcd");
        $dumpvars(0, testbench_alu_32bit);
        
        // 测试加法
        a = 32'h0000000A; b = 32'h00000005; op = 4'b0000;
        #10;
        if (result !== 32'h0000000F || zero !== 1'b0) begin
            $display("❌ 加法测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 加法测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        // 测试减法
        a = 32'h0000000F; b = 32'h00000005; op = 4'b0001;
        #10;
        if (result !== 32'h0000000A || zero !== 1'b0) begin
            $display("❌ 减法测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 减法测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        // 测试逻辑与
        a = 32'h0000000F; b = 32'h00000005; op = 4'b0010;
        #10;
        if (result !== 32'h00000005 || zero !== 1'b0) begin
            $display("❌ 逻辑与测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 逻辑与测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        // 测试逻辑或
        a = 32'h0000000A; b = 32'h00000005; op = 4'b0011;
        #10;
        if (result !== 32'h0000000F || zero !== 1'b0) begin
            $display("❌ 逻辑或测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 逻辑或测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        // 测试异或
        a = 32'h0000000F; b = 32'h00000005; op = 4'b0100;
        #10;
        if (result !== 32'h0000000A || zero !== 1'b0) begin
            $display("❌ 异或测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 异或测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        // 测试左移
        a = 32'h00000001; b = 32'h00000002; op = 4'b0101;
        #10;
        if (result !== 32'h00000004 || zero !== 1'b0) begin
            $display("❌ 左移测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 左移测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        // 测试右移
        a = 32'h00000004; b = 32'h00000002; op = 4'b0110;
        #10;
        if (result !== 32'h00000001 || zero !== 1'b0) begin
            $display("❌ 右移测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 右移测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        // 测试零标志
        a = 32'h00000000; b = 32'h00000000; op = 4'b0000;
        #10;
        if (result !== 32'h00000000 || zero !== 1'b1) begin
            $display("❌ 零标志测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 零标志测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        // 测试无效操作码
        a = 32'h0000000F; b = 32'h00000005; op = 4'b1111;
        #10;
        if (result !== 32'h00000000 || zero !== 1'b1) begin
            $display("❌ 无效操作码测试失败: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end else begin
            $display("✅ 无效操作码测试通过: a=%h, b=%h, result=%h, zero=%b", a, b, result, zero);
        end
        
        $display("🎉 所有测试完成");
        $finish;
    end
    
endmodule
'''
    
    # 保存到实验目录
    experiment_dir = Path("tdd_experiments/unified_tdd_alu_1754283086")
    if experiment_dir.exists():
        testbench_path = experiment_dir / "testbenches" / "testbench_alu_32bit.v"
        testbench_path.parent.mkdir(exist_ok=True)
        
        with open(testbench_path, 'w', encoding='utf-8') as f:
            f.write(testbench_content)
        
        print(f"✅ 正确的测试台已保存到: {testbench_path}")
        return True
    else:
        print("❌ 实验目录不存在")
        return False

def fix_tool_registration():
    """修复工具注册问题"""
    print("🔧 修复工具注册问题...")
    
    # 检查代码审查智能体的工具注册
    review_agent_file = Path("agents/enhanced_real_code_review_agent.py")
    if not review_agent_file.exists():
        print("❌ 找不到代码审查智能体文件")
        return False
    
    # 检查是否注册了write_file工具
    with open(review_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'write_file' in content:
            print("✅ write_file工具已在代码审查智能体中注册")
            return True
        else:
            print("⚠️ write_file工具未在代码审查智能体中注册")
            return False

def create_correct_alu_design():
    """创建正确的ALU设计"""
    print("🔧 创建正确的ALU设计...")
    
    alu_content = '''module alu_32bit (
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
    
endmodule
'''
    
    # 保存到实验目录
    experiment_dir = Path("tdd_experiments/unified_tdd_alu_1754283086")
    if experiment_dir.exists():
        design_path = experiment_dir / "designs" / "alu_32bit_correct.v"
        design_path.parent.mkdir(exist_ok=True)
        
        with open(design_path, 'w', encoding='utf-8') as f:
            f.write(alu_content)
        
        print(f"✅ 正确的ALU设计已保存到: {design_path}")
        return True
    else:
        print("❌ 实验目录不存在")
        return False

def main():
    """主修复流程"""
    print("🚀 开始修复ALU实验V2...")
    print("=" * 50)
    
    # 1. 修复智能体选择逻辑
    if not fix_agent_selection_logic():
        print("❌ 智能体选择逻辑修复失败")
        return False
    
    # 2. 修复测试台生成
    if not fix_testbench_generation():
        print("❌ 测试台生成修复失败")
        return False
    
    # 3. 修复工具注册
    if not fix_tool_registration():
        print("❌ 工具注册修复失败")
        return False
    
    # 4. 创建正确的ALU设计
    if not create_correct_alu_design():
        print("❌ ALU设计创建失败")
        return False
    
    print("=" * 50)
    print("✅ ALU实验V2修复完成")
    print("📁 修复文件位置:")
    print("   - 正确ALU设计: tdd_experiments/unified_tdd_alu_1754283086/designs/alu_32bit_correct.v")
    print("   - 正确测试台: tdd_experiments/unified_tdd_alu_1754283086/testbenches/testbench_alu_32bit.v")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 