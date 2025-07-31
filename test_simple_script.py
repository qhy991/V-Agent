#!/usr/bin/env python3
"""
简单脚本功能测试
Simple Script Functionality Test
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.real_code_reviewer import RealCodeReviewAgent
from config.config import FrameworkConfig
from core.enhanced_logging_config import setup_enhanced_logging

async def test_simple_script():
    """测试基础脚本功能"""
    
    # 初始化增强日志系统
    log_session = setup_enhanced_logging("simple_script_test")
    print(f"📁 实验目录: {log_session.session_log_dir}")
    
    try:
        # 初始化智能体
        config = FrameworkConfig.from_env()
        review_agent = RealCodeReviewAgent(config)
        
        # 创建简单的测试文件
        artifacts_dir = log_session.session_log_dir / "artifacts"
        
        # 创建一个简单的Verilog模块
        simple_module = """module and_gate(
    input a, b,
    output y
);
    assign y = a & b;
endmodule"""
        
        simple_testbench = """module and_gate_tb;
    reg a, b;
    wire y;
    
    and_gate uut (.a(a), .b(b), .y(y));
    
    initial begin
        $display("Testing AND gate");
        a = 0; b = 0; #10; $display("0 & 0 = %b", y);
        a = 0; b = 1; #10; $display("0 & 1 = %b", y);
        a = 1; b = 0; #10; $display("1 & 0 = %b", y);
        a = 1; b = 1; #10; $display("1 & 1 = %b", y);
        $finish;
    end
endmodule"""
        
        # 保存文件
        with open(artifacts_dir / "and_gate.v", 'w') as f:
            f.write(simple_module)
        with open(artifacts_dir / "and_gate_tb.v", 'w') as f:
            f.write(simple_testbench)
        
        print("📝 已创建测试文件")
        
        # 生成脚本
        print("🔨 生成构建脚本...")
        script_result = await review_agent._tool_write_build_script(
            verilog_files=["and_gate.v"],
            testbench_files=["and_gate_tb.v"], 
            script_type="bash",
            target_name="and_gate_sim"
        )
        
        if script_result["success"]:
            print(f"✅ 脚本生成成功: {script_result['script_name']}")
            
            # 执行脚本
            print("⚡ 执行构建脚本...")
            exec_result = await review_agent._tool_execute_build_script(
                script_name=script_result["script_name"],
                action="all"
            )
            
            print(f"📋 执行结果: {'成功' if exec_result['success'] else '失败'}")
            print(f"📋 返回码: {exec_result['return_code']}")
            
            if exec_result.get("stdout"):
                print("\n📤 标准输出:")
                print(exec_result["stdout"])
            
            if exec_result.get("stderr") and exec_result["stderr"].strip():
                print("\n📤 标准错误:")
                print(exec_result["stderr"])
            
            return exec_result["success"]
        else:
            print(f"❌ 脚本生成失败: {script_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_script())
    print(f"\n🎯 测试结果: {'成功' if success else '失败'}")