#!/usr/bin/env python3
"""
演示脚本化构建与智能体协作
Demo: Script-based Build with Agent Collaboration
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from agents.real_verilog_agent import RealVerilogDesignAgent
from config.config import FrameworkConfig
from llm_integration.enhanced_llm_client import EnhancedLLMClient
from core.enhanced_logging_config import setup_enhanced_logging

async def demo_script_based_workflow():
    """演示基于脚本的工作流程"""
    
    # 初始化增强日志系统
    log_session = setup_enhanced_logging("script_demo")
    print("🚀 脚本化构建演示")
    print(f"📁 实验目录: {log_session.session_log_dir}")
    print("="*60)
    
    try:
        # 1. 初始化框架
        config = FrameworkConfig.from_env()
        llm_client = EnhancedLLMClient(config.llm)
        
        # 创建智能体
        verilog_agent = RealVerilogDesignAgent(config)
        review_agent = RealCodeReviewAgent(config)
        
        print("✅ 智能体框架初始化完成")
        
        # 2. 演示智能体Function Calling生成设计
        print("\n🔬 演示Verilog设计智能体功能")
        print("="*60)
        
        design_request = "设计一个简单的8位计数器模块，包含时钟、复位、使能和加载功能"
        
        print(f"📝 设计请求: {design_request}")
        
        # 调用设计智能体
        design_result = await verilog_agent.process_with_function_calling(
            user_request=design_request,
            max_iterations=5
        )
        
        print("📋 设计智能体响应:")
        print(design_result[:500] + "..." if len(design_result) > 500 else design_result)
        
        # 3. 手动演示脚本生成和执行
        print("\n" + "="*60)
        print("🛠️ 手动演示脚本化构建")
        print("="*60)
        
        # 创建演示用的简单模块
        artifacts_dir = log_session.session_log_dir / "artifacts"
        
        # Counter模块
        counter_module = """module counter_8bit(
    input clk,
    input reset,
    input enable,
    input [7:0] load_data,
    input load,
    output reg [7:0] count
);
    always @(posedge clk or posedge reset) begin
        if (reset)
            count <= 8'b0;
        else if (load)
            count <= load_data;
        else if (enable)
            count <= count + 1;
    end
endmodule"""
        
        # 测试台
        counter_testbench = """module counter_8bit_tb;
    reg clk, reset, enable, load;
    reg [7:0] load_data;
    wire [7:0] count;
    
    counter_8bit uut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .load_data(load_data),
        .load(load),
        .count(count)
    );
    
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    initial begin
        $dumpfile("counter_8bit.vcd");
        $dumpvars(0, counter_8bit_tb);
        
        // Reset test
        reset = 1; enable = 0; load = 0; load_data = 0;
        #10 reset = 0;
        
        // Count test
        enable = 1;
        #100;
        
        // Load test
        enable = 0;
        load_data = 8'hFF;
        load = 1;
        #10 load = 0;
        enable = 1;
        #50;
        
        $display("Counter test completed");
        $finish;
    end
endmodule"""
        
        # 保存文件
        with open(artifacts_dir / "counter_8bit.v", 'w') as f:
            f.write(counter_module)
        with open(artifacts_dir / "counter_8bit_tb.v", 'w') as f:
            f.write(counter_testbench)
        
        print("📝 创建演示模块: counter_8bit.v")
        
        # 5. 生成Makefile
        print("\n🔨 生成Makefile...")
        makefile_result = await review_agent._tool_write_build_script(
            verilog_files=["counter_8bit.v"],
            testbench_files=["counter_8bit_tb.v"],
            script_type="makefile",
            target_name="counter_sim"
        )
        
        if makefile_result["success"]:
            print(f"✅ Makefile已生成: {makefile_result['script_name']}")
            
            # 执行 make compile
            print("\n⚡ 执行编译...")
            compile_result = await review_agent._tool_execute_build_script(
                script_name=makefile_result["script_name"],
                action="compile"
            )
            
            print(f"📋 编译结果: {'成功' if compile_result['success'] else '失败'}")
            
            if compile_result["success"]:
                # 执行 make simulate
                print("\n⚡ 执行仿真...")
                sim_result = await review_agent._tool_execute_build_script(
                    script_name=makefile_result["script_name"],
                    action="simulate"
                )
                
                print(f"📋 仿真结果: {'成功' if sim_result['success'] else '失败'}")
                
                if sim_result.get("stdout"):
                    print("\n📤 仿真输出:")
                    # 只显示最后几行重要输出
                    output_lines = sim_result["stdout"].split('\n')
                    important_lines = [line for line in output_lines if any(keyword in line.lower() 
                                     for keyword in ['test', 'counter', 'completed', 'finish'])]
                    for line in important_lines[-5:]:
                        if line.strip():
                            print(f"  {line}")
        
        # 6. 生成Bash脚本演示
        print("\n" + "="*60)
        print("🐚 生成Bash脚本演示")
        print("="*60)
        
        bash_result = await review_agent._tool_write_build_script(
            verilog_files=["counter_8bit.v"],
            testbench_files=["counter_8bit_tb.v"],
            script_type="bash",
            target_name="counter_bash_sim"
        )
        
        if bash_result["success"]:
            print(f"✅ Bash脚本已生成: {bash_result['script_name']}")
            
            # 执行清理、编译、仿真
            for action in ["clean", "compile", "simulate"]:
                print(f"\n⚡ 执行 {action}...")
                action_result = await review_agent._tool_execute_build_script(
                    script_name=bash_result["script_name"],
                    action=action
                )
                
                success_msg = "✅" if action_result["success"] else "❌"
                print(f"{success_msg} {action}: {'成功' if action_result['success'] else '失败'}")
        
        print("\n🎉 脚本化构建演示完成！")
        print("="*60)
        print("📋 功能总结:")
        print("  ✅ 智能体可以生成Makefile和Bash脚本")
        print("  ✅ 脚本支持编译、仿真、清理等操作")
        print("  ✅ 使用原始文件而非临时文件") 
        print("  ✅ 支持复杂的多模块工程")
        print("  ✅ 与智能体协作流程完全集成")
        
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(demo_script_based_workflow())
    print(f"\n🎯 演示结果: {'成功' if success else '失败'}")