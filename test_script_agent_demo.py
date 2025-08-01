#!/usr/bin/env python3
"""
脚本工具测试演示程序
演示agent如何使用脚本工具进行Verilog项目构建和仿真
"""

import asyncio
import os
import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入框架组件
from config.config import FrameworkConfig
from agents.real_code_reviewer import RealCodeReviewAgent
from agents.real_verilog_agent import RealVerilogDesignAgent
from tools.script_tools import ScriptManager


class ScriptToolDemo:
    """脚本工具演示类"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        self.script_manager = ScriptManager()
        self.temp_dir = None
        
    async def setup_demo_environment(self):
        """设置演示环境"""
        # 创建临时工作目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix="script_demo_"))
        print(f"🎯 创建演示目录: {self.temp_dir}")
        
        # 创建示例Verilog项目
        await self.create_sample_verilog_project()
        
    async def create_sample_verilog_project(self):
        """创建示例Verilog项目"""
        verilog_dir = self.temp_dir / "verilog"
        verilog_dir.mkdir(exist_ok=True)
        
        # 创建简单的8位计数器
        counter_v = verilog_dir / "counter.v"
        counter_content = """
module counter (
    input wire clk,
    input wire reset,
    input wire enable,
    output reg [7:0] count,
    output wire overflow
);

assign overflow = (count == 8'hFF);

always @(posedge clk or posedge reset) begin
    if (reset) begin
        count <= 8'h00;
    end else if (enable) begin
        count <= count + 8'h01;
    end
end

endmodule
"""
        counter_v.write_text(counter_content.strip())
        
        # 创建测试台
        tb_v = verilog_dir / "counter_tb.v"
        tb_content = """
`timescale 1ns / 1ps

module counter_tb;
    reg clk;
    reg reset;
    reg enable;
    wire [7:0] count;
    wire overflow;

    // 实例化被测试模块
    counter dut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .count(count),
        .overflow(overflow)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // 测试激励
    initial begin
        // 初始化
        reset = 1;
        enable = 0;
        #20;
        
        // 释放复位，开始计数
        reset = 0;
        enable = 1;
        
        // 等待足够长的时间让计数器计数
        #1000;
        
        // 停止仿真
        $finish;
    end

    // 监控输出
    initial begin
        $monitor("Time=%0t reset=%b enable=%b count=%d overflow=%b", 
                 $time, reset, enable, count, overflow);
    end

    // 生成波形
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);
    end

endmodule
"""
        tb_v.write_text(tb_content.strip())
        
        print(f"✅ 创建示例项目文件:")
        print(f"   - {counter_v}")
        print(f"   - {tb_v}")
        
    async def demo_script_generation(self):
        """演示脚本生成功能"""
        print("\n🚀 开始脚本生成演示...")
        
        # 使用代码审查智能体生成构建脚本
        reviewer = RealCodeReviewAgent(self.config)
        
        # 准备文件列表
        verilog_files = [str(self.temp_dir / "verilog" / "counter.v")]
        testbench_files = [str(self.temp_dir / "verilog" / "counter_tb.v")]
        
        # 生成bash脚本
        bash_script_result = await reviewer._tool_write_build_script(
            verilog_files=verilog_files,
            testbench_files=testbench_files,
            target_name="counter_sim",
            script_type="bash",
            include_wave_generation=True
        )
        
        if bash_script_result["success"]:
            print(f"✅ Bash脚本生成成功: {bash_script_result['result']['script_path']}")
        
        # 生成Makefile
        makefile_result = await reviewer._tool_write_build_script(
            verilog_files=verilog_files,
            testbench_files=testbench_files,
            target_name="counter_sim",
            script_type="makefile",
            include_wave_generation=True
        )
        
        if makefile_result["success"]:
            print(f"✅ Makefile生成成功: {makefile_result['result']['script_path']}")
            
    async def demo_script_execution(self):
        """演示脚本执行功能"""
        print("\n⚙️ 开始脚本执行演示...")
        
        # 执行bash脚本
        scripts_dir = self.temp_dir / "scripts"
        if scripts_dir.exists():
            build_script = scripts_dir / "build_counter_sim_bash.sh"
            
            if build_script.exists():
                print(f"🎯 执行脚本: {build_script}")
                
                # 使用脚本管理器执行
                result = await self.script_manager.execute_script(
                    str(build_script),
                    working_directory=str(self.temp_dir),
                    timeout=30
                )
                
                if result["success"]:
                    print("✅ 脚本执行成功!")
                    print("📊 执行结果:")
                    print(result["stdout"])
                    
                    # 检查生成的文件
                    vcd_file = self.temp_dir / "counter_tb.vcd"
                    if vcd_file.exists():
                        print(f"📈 波形文件已生成: {vcd_file}")
                else:
                    print("❌ 脚本执行失败:")
                    print(result["stderr"])
                    
    async def demo_agent_with_function_calling(self):
        """演示智能体使用Function Calling调用脚本工具"""
        print("\n🤖 开始智能体Function Calling演示...")
        
        # 创建Verilog设计智能体
        verilog_agent = RealVerilogDesignAgent(self.config)
        reviewer_agent = RealCodeReviewAgent(self.config)
        
        # 模拟用户请求
        user_request = f"""
        请为以下Verilog项目创建完整的构建和仿真环境：
        - 设计文件: {self.temp_dir}/verilog/counter.v
        - 测试文件: {self.temp_dir}/verilog/counter_tb.v
        - 需要: 生成构建脚本并执行仿真
        """
        
        print(f"🎯 用户请求: {user_request}")
        
        # 使用Verilog设计智能体生成项目
        design_response = await verilog_agent.process_with_function_calling(
            user_request="创建一个8位计数器设计",
            max_iterations=3
        )
        
        print("📋 Verilog设计智能体响应:")
        print(json.dumps(design_response, indent=2, ensure_ascii=False))
        
        # 使用审查智能体创建测试环境
        review_response = await reviewer_agent.process_with_function_calling(
            user_request=user_request,
            max_iterations=5
        )
        
        print("📋 代码审查智能体响应:")
        print(json.dumps(review_response, indent=2, ensure_ascii=False))
        
    def list_generated_files(self):
        """列出生成的文件"""
        print(f"\n📁 项目文件结构:")
        
        def print_directory_tree(path, prefix=""):
            items = sorted(path.iterdir())
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                
                if item.is_dir():
                    print(f"{prefix}{connector}{item.name}/")
                    extension = "    " if is_last else "│   "
                    print_directory_tree(item, prefix + extension)
                else:
                    print(f"{prefix}{connector}{item.name}")
        
        print_directory_tree(self.temp_dir)
        
    async def cleanup(self):
        """清理临时文件"""
        if self.temp_dir and self.temp_dir.exists():
            print(f"\n🧹 清理临时目录: {self.temp_dir}")
            # 注意：实际使用时可以删除，这里保留用于检查
            # import shutil
            # shutil.rmtree(self.temp_dir)


async def main():
    """主测试函数"""
    print("🚀 CentralizedAgentFramework 脚本工具测试演示")
    print("=" * 50)
    
    demo = ScriptToolDemo()
    
    try:
        # 设置环境
        await demo.setup_demo_environment()
        
        # 演示1: 脚本生成
        await demo.demo_script_generation()
        
        # 演示2: 脚本执行
        await demo.demo_script_execution()
        
        # 演示3: 智能体Function Calling
        await demo.demo_agent_with_function_calling()
        
        # 显示文件结构
        demo.list_generated_files()
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理（可选）
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())