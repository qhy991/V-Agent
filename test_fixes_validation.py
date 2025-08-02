#!/usr/bin/env python3
"""
测试修复验证
Validation Test for TDD Fixes
"""

import asyncio
import tempfile
import subprocess
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_dependency_resolution():
    """测试依赖解析修复"""
    print("🔍 测试依赖解析修复")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建four_bit_adder.v (依赖full_adder)
        four_bit_adder = temp_path / "four_bit_adder.v"
        four_bit_adder.write_text("""
module four_bit_adder (
    input [3:0] a,
    input [3:0] b,
    input cin,
    output [3:0] sum,
    output cout
);

    wire c1, c2, c3;

    // 一位全加器
    full_adder fa0 (.a(a[0]), .b(b[0]), .cin(cin), .sum(sum[0]), .cout(c1));
    full_adder fa1 (.a(a[1]), .b(b[1]), .cin(c1), .sum(sum[1]), .cout(c2));
    full_adder fa2 (.a(a[2]), .b(b[2]), .cin(c2), .sum(sum[2]), .cout(c3));
    full_adder fa3 (.a(a[3]), .b(b[3]), .cin(c3), .sum(sum[3]), .cout(cout));

endmodule

// 一位全加器模块
module full_adder (
    input a,
    input b,
    input cin,
    output sum,
    output cout
);

    assign sum = a ^ b ^ cin;
    assign cout = (a & b) | (b & cin) | (a & cin);

endmodule
""")
        
        # 创建测试台
        testbench = temp_path / "four_bit_adder_tb.v"
        testbench.write_text("""
module four_bit_adder_tb;
    reg [3:0] a, b;
    reg cin;
    wire [3:0] sum;
    wire cout;
    
    four_bit_adder uut (.a(a), .b(b), .cin(cin), .sum(sum), .cout(cout));
    
    initial begin
        $dumpfile("test.vcd");
        $dumpvars(0, four_bit_adder_tb);
        
        a = 4'b0000; b = 4'b0000; cin = 0; #10;
        a = 4'b0001; b = 4'b0001; cin = 0; #10;
        a = 4'b1111; b = 4'b0001; cin = 0; #10;
        a = 4'b1111; b = 4'b1111; cin = 1; #10;
        
        $finish;
    end
    
endmodule
""")
        
        # 测试Enhanced Code Reviewer的依赖分析
        try:
            from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
            from config.config import FrameworkConfig
            
            config = FrameworkConfig.from_env()
            reviewer = EnhancedRealCodeReviewAgent(config)
            
            # 测试run_simulation工具调用
            result = await reviewer._tool_run_simulation(
                module_file=str(four_bit_adder),
                testbench_file=str(testbench),
                simulator="iverilog"
            )
            
            print(f"仿真结果: {result.get('success', False)}")
            if result.get('success'):
                print("✅ 依赖分析修复成功：仿真正常运行")
            else:
                print(f"❌ 仿真失败: {result.get('error', 'Unknown error')}")
                print(f"详细信息: {result.get('details', {})}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")

async def test_error_handling_fix():
    """测试错误处理修复"""
    print("\n🧪 测试错误处理修复")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建有错误的模块（缺少依赖）
        broken_module = temp_path / "broken_module.v"
        broken_module.write_text("""
module broken_module (
    input a,
    input b,
    output y
);
    
    // 引用不存在的模块
    missing_module inst1 (.in1(a), .in2(b), .out(y));
    
endmodule
""")
        
        # 创建测试台
        testbench = temp_path / "broken_module_tb.v"
        testbench.write_text("""
module broken_module_tb;
    reg a, b;
    wire y;
    
    broken_module uut (.a(a), .b(b), .y(y));
    
    initial begin
        a = 0; b = 0; #10;
        $finish;
    end
    
endmodule
""")
        
        try:
            from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
            from config.config import FrameworkConfig
            
            config = FrameworkConfig.from_env()
            reviewer = EnhancedRealCodeReviewAgent(config)
            
            # 测试失败情况的错误处理
            result = await reviewer._tool_run_simulation(
                module_file=str(broken_module),
                testbench_file=str(testbench),
                simulator="iverilog"
            )
            
            if result.get('success') == False:
                print("✅ 错误处理修复成功：正确报告失败状态")
                error_msg = result.get('error', '')
                if 'missing_module' in error_msg or 'not found' in error_msg:
                    print("✅ 错误信息正确：包含具体错误详情")
                else:
                    print(f"⚠️ 错误信息: {error_msg}")
            else:
                print("❌ 错误处理失败：应该报告失败但返回成功")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")

async def test_experiment_manager_integration():
    """测试实验管理器集成"""
    print("\n📁 测试实验管理器集成")
    
    try:
        from core.experiment_manager import ExperimentManager
        
        # 创建实验管理器
        exp_manager = ExperimentManager()
        
        # 创建测试实验
        exp_path = exp_manager.create_new_experiment(
            experiment_name="validation_test",
            description="修复验证测试"
        )
        
        print(f"✅ 创建实验: {exp_path.name}")
        
        # 保存测试文件
        test_content = "module test_module; endmodule"
        saved_path = exp_manager.save_file(
            content=test_content,
            filename="test_module.v",
            subdir="designs",
            description="测试模块"
        )
        
        if saved_path and saved_path.exists():
            print("✅ 文件保存成功")
        else:
            print("❌ 文件保存失败")
            
        # 获取实验摘要
        summary = exp_manager.get_experiment_summary()
        print(f"✅ 实验摘要: {summary.get('experiment_name', 'unknown')}")
        
        # 结束实验
        exp_manager.finish_experiment(success=True, final_notes="验证测试完成")
        
        final_summary = exp_manager.get_experiment_summary()
        print(f"✅ 最终状态: {final_summary.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 实验管理器测试失败: {e}")

async def main():
    """主测试函数"""
    print("🎯 开始修复验证测试")
    print("="*60)
    
    await test_dependency_resolution()
    await test_error_handling_fix()
    await test_experiment_manager_integration()
    
    print("\n" + "="*60)
    print("🎉 修复验证测试完成")

if __name__ == "__main__":
    asyncio.run(main())