#!/usr/bin/env python3
"""
脚本工具测试
Test Script Tools Functionality
"""

import asyncio
import json
import logging
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.centralized_coordinator import CentralizedCoordinator
from agents.real_code_reviewer import RealCodeReviewAgent
from agents.real_verilog_agent import RealVerilogDesignAgent
from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from core.enhanced_logging_config import setup_enhanced_logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_script_generation_and_execution():
    """测试脚本生成和执行功能"""
    
    # 初始化增强日志系统
    log_session = setup_enhanced_logging("script_test")
    print(f"📁 实验目录: {log_session.session_log_dir}")
    
    try:
        # 1. 初始化配置和智能体
        config = FrameworkConfig.from_env()
        llm_client = EnhancedLLMClient(config.llm)
        
        # 创建智能体
        review_agent = RealCodeReviewAgent(config)
        logger.info("✅ 代码审查智能体初始化完成")
        
        # 2. 创建简单的测试Verilog文件
        test_verilog_content = """module simple_adder(
    input [3:0] a,
    input [3:0] b,
    input cin,
    output [3:0] sum,
    output cout
);
    assign {cout, sum} = a + b + cin;
endmodule"""
        
        test_testbench_content = """module simple_adder_tb;
    reg [3:0] a, b;
    reg cin;
    wire [3:0] sum;
    wire cout;
    
    simple_adder uut (
        .a(a),
        .b(b), 
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );
    
    initial begin
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, simple_adder_tb);
        
        // Test cases
        a = 4'b0001; b = 4'b0010; cin = 0; #10;
        $display("Test 1: %d + %d + %d = %d (cout=%d)", a, b, cin, sum, cout);
        
        a = 4'b1111; b = 4'b0001; cin = 0; #10;
        $display("Test 2: %d + %d + %d = %d (cout=%d)", a, b, cin, sum, cout);
        
        a = 4'b1111; b = 4'b1111; cin = 1; #10;
        $display("Test 3: %d + %d + %d = %d (cout=%d)", a, b, cin, sum, cout);
        
        $finish;
    end
endmodule"""
        
        # 3. 保存测试文件
        artifacts_dir = log_session.session_log_dir / "artifacts"
        verilog_file = artifacts_dir / "simple_adder.v"
        testbench_file = artifacts_dir / "simple_adder_tb.v"
        
        with open(verilog_file, 'w') as f:
            f.write(test_verilog_content)
        with open(testbench_file, 'w') as f:
            f.write(test_testbench_content)
        
        logger.info(f"📝 创建测试文件: {verilog_file}")
        logger.info(f"📝 创建测试文件: {testbench_file}")
        
        # 4. 测试生成Bash脚本
        print("\n" + "="*60)
        print("🧪 测试1: 生成Bash构建脚本")
        print("="*60)
        
        bash_result = await review_agent._tool_write_build_script(
            verilog_files=["simple_adder.v"],
            testbench_files=["simple_adder_tb.v"],
            script_type="bash",
            target_name="simple_adder_sim"
        )
        
        print(f"📋 Bash脚本生成结果:")
        print(json.dumps(bash_result, indent=2, ensure_ascii=False))
        
        # 5. 测试生成Makefile
        print("\n" + "="*60)
        print("🧪 测试2: 生成Makefile")
        print("="*60)
        
        makefile_result = await review_agent._tool_write_build_script(
            verilog_files=["simple_adder.v"],
            testbench_files=["simple_adder_tb.v"],
            script_type="makefile",
            target_name="simple_adder_sim"
        )
        
        print(f"📋 Makefile生成结果:")
        print(json.dumps(makefile_result, indent=2, ensure_ascii=False))
        
        # 6. 测试执行Bash脚本
        if bash_result.get("success"):
            print("\n" + "="*60)
            print("🧪 测试3: 执行Bash脚本")
            print("="*60)
            
            bash_exec_result = await review_agent._tool_execute_build_script(
                script_name=bash_result["script_name"],
                action="all"
            )
            
            print(f"📋 Bash脚本执行结果:")
            print(json.dumps({
                "success": bash_exec_result["success"],
                "return_code": bash_exec_result["return_code"],
                "command": bash_exec_result["command"],
                "message": bash_exec_result["message"]
            }, indent=2, ensure_ascii=False))
            
            if bash_exec_result.get("stdout"):
                print(f"\n📤 标准输出:")
                print(bash_exec_result["stdout"])
            
            if bash_exec_result.get("stderr"):
                print(f"\n📤 标准错误:")
                print(bash_exec_result["stderr"])
        
        # 7. 测试执行Makefile
        if makefile_result.get("success"):
            print("\n" + "="*60)
            print("🧪 测试4: 执行Makefile")
            print("="*60)
            
            make_exec_result = await review_agent._tool_execute_build_script(
                script_name=makefile_result["script_name"],
                action="all"
            )
            
            print(f"📋 Makefile执行结果:")
            print(json.dumps({
                "success": make_exec_result["success"],
                "return_code": make_exec_result["return_code"],
                "command": make_exec_result["command"],
                "message": make_exec_result["message"]
            }, indent=2, ensure_ascii=False))
            
            if make_exec_result.get("stdout"):
                print(f"\n📤 标准输出:")
                print(make_exec_result["stdout"])
            
            if make_exec_result.get("stderr"):
                print(f"\n📤 标准错误:")
                print(make_exec_result["stderr"])
        
        # 8. 测试复杂的多模块工程
        print("\n" + "="*60)
        print("🧪 测试5: 复杂多模块工程")
        print("="*60)
        
        # 创建一个复杂的多模块设计
        full_adder_content = """module full_adder(
    input a, b, cin,
    output sum, cout
);
    assign sum = a ^ b ^ cin;
    assign cout = (a & b) | (cin & (a ^ b));
endmodule"""
        
        four_bit_adder_content = """module four_bit_adder(
    input [3:0] a, b,
    input cin,
    output [3:0] sum,
    output cout
);
    wire [2:0] carry;
    
    full_adder fa0 (.a(a[0]), .b(b[0]), .cin(cin), .sum(sum[0]), .cout(carry[0]));
    full_adder fa1 (.a(a[1]), .b(b[1]), .cin(carry[0]), .sum(sum[1]), .cout(carry[1]));
    full_adder fa2 (.a(a[2]), .b(b[2]), .cin(carry[1]), .sum(sum[2]), .cout(carry[2]));
    full_adder fa3 (.a(a[3]), .b(b[3]), .cin(carry[2]), .sum(sum[3]), .cout(cout));
endmodule"""
        
        multi_testbench_content = """module four_bit_adder_tb;
    reg [3:0] a, b;
    reg cin;
    wire [3:0] sum;
    wire cout;
    
    four_bit_adder uut (
        .a(a), .b(b), .cin(cin),
        .sum(sum), .cout(cout)
    );
    
    initial begin
        $dumpfile("four_bit_adder.vcd");
        $dumpvars(0, four_bit_adder_tb);
        
        // Comprehensive test cases
        $display("Starting 4-bit adder tests...");
        
        a = 4'b0000; b = 4'b0000; cin = 0; #10;
        $display("Test: %b + %b + %b = %b (cout=%b)", a, b, cin, sum, cout);
        
        a = 4'b0101; b = 4'b1010; cin = 0; #10;
        $display("Test: %b + %b + %b = %b (cout=%b)", a, b, cin, sum, cout);
        
        a = 4'b1111; b = 4'b0001; cin = 0; #10;
        $display("Test: %b + %b + %b = %b (cout=%b)", a, b, cin, sum, cout);
        
        a = 4'b1111; b = 4'b1111; cin = 1; #10;
        $display("Test: %b + %b + %b = %b (cout=%b)", a, b, cin, sum, cout);
        
        $display("All tests completed.");
        $finish;
    end
endmodule"""
        
        # 保存多模块文件
        full_adder_file = artifacts_dir / "full_adder.v"
        four_bit_adder_file = artifacts_dir / "four_bit_adder.v"
        multi_testbench_file = artifacts_dir / "four_bit_adder_tb.v"
        
        with open(full_adder_file, 'w') as f:
            f.write(full_adder_content)
        with open(four_bit_adder_file, 'w') as f:
            f.write(four_bit_adder_content)
        with open(multi_testbench_file, 'w') as f:
            f.write(multi_testbench_content)
        
        # 生成多模块构建脚本
        multi_bash_result = await review_agent._tool_write_build_script(
            verilog_files=["full_adder.v", "four_bit_adder.v"],
            testbench_files=["four_bit_adder_tb.v"],
            script_type="bash",
            target_name="multi_module_sim"
        )
        
        print(f"📋 多模块Bash脚本生成: {'成功' if multi_bash_result['success'] else '失败'}")
        
        # 执行多模块脚本
        if multi_bash_result.get("success"):
            multi_exec_result = await review_agent._tool_execute_build_script(
                script_name=multi_bash_result["script_name"],
                action="all"
            )
            
            print(f"📋 多模块脚本执行: {'成功' if multi_exec_result['success'] else '失败'}")
            if multi_exec_result.get("stdout"):
                print("📤 仿真输出:")
                print(multi_exec_result["stdout"][-500:])  # 显示最后500字符
        
        print("\n🎉 脚本工具测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_script_generation_and_execution())
    if success:
        print("✅ 所有测试通过")
    else:
        print("❌ 测试失败")
        sys.exit(1)