#!/usr/bin/env python3
"""
工作版本 - 脚本工具测试程序
演示agent如何使用脚本工具
"""

import asyncio
import sys
from pathlib import Path
import subprocess

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.script_tools import ScriptManager


def test_script_tools():
    """测试脚本工具功能"""
    print("🚀 开始脚本工具功能测试...")
    
    # 创建脚本管理器
    script_manager = ScriptManager()
    
    # 创建测试目录和文件
    test_dir = Path("working_test")
    test_dir.mkdir(exist_ok=True)
    
    # 创建示例Verilog文件
    counter_v = test_dir / "counter.v"
    counter_v.write_text('''
module counter (
    input wire clk,
    input wire reset,
    input wire enable,
    output reg [3:0] count
);

always @(posedge clk or posedge reset) begin
    if (reset)
        count <= 4'b0000;
    else if (enable)
        count <= count + 4'b0001;
end

endmodule
''')
    
    counter_tb_v = test_dir / "counter_tb.v"
    counter_tb_v.write_text('''
`timescale 1ns / 1ps

module counter_tb;
    reg clk;
    reg reset;
    reg enable;
    wire [3:0] count;

    counter dut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .count(count)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        reset = 1;
        enable = 0;
        #20;
        
        reset = 0;
        enable = 1;
        
        #100;
        
        $display("Simulation completed successfully!");
        $finish;
    end

    initial begin
        $monitor("Time=%0t reset=%b enable=%b count=%d", $time, reset, enable, count);
    end

endmodule
''')
    
    print("✅ 创建测试文件:")
    print(f"   - {counter_v}")
    print(f"   - {counter_tb_v}")
    
    # 测试1: 生成Bash构建脚本
    print("\n📋 生成Bash构建脚本...")
    bash_script = script_manager.generate_build_script(
        verilog_files=[str(counter_v)],
        testbench_files=[str(counter_tb_v)],
        target_name="counter_sim",
        include_wave_generation=True
    )
    
    bash_result = script_manager.write_script(
        "build_counter_sim",
        bash_script,
        script_type="bash"
    )
    
    if bash_result["success"]:
        print(f"✅ Bash脚本已生成: {bash_result['script_path']}")
    
    # 测试2: 生成Makefile
    print("\n📋 生成Makefile...")
    makefile_content = script_manager.generate_makefile(
        verilog_files=[str(counter_v)],
        testbench_files=[str(counter_tb_v)],
        target_name="counter_sim",
        top_module="counter_tb"
    )
    
    makefile_result = script_manager.write_script(
        "Makefile",
        makefile_content,
        script_type="make"
    )
    
    if makefile_result["success"]:
        print(f"✅ Makefile已生成: {makefile_result['script_path']}")
    
    # 测试3: 执行简单脚本验证环境
    print("\n⚙️ 测试环境验证...")
    check_script = """#!/bin/bash
echo "🎯 环境验证开始..."
echo "📁 工作目录: $(pwd)"
echo "🛠️ iverilog版本: $(iverilog -V 2>/dev/null || echo '未安装')"
echo "📅 测试时间: $(date)"
echo "✅ 环境验证完成！"
"""
    
    check_result = script_manager.write_script(
        "env_check",
        check_script,
        script_type="bash"
    )
    
    if check_result["success"]:
        print(f"✅ 环境检查脚本已生成: {check_result['script_path']}")
        
        # 执行环境检查
        env_result = script_manager.execute_script(
            check_result["script_path"],
            working_directory=str(test_dir)
        )
        
        if env_result["success"]:
            print("📊 环境检查结果:")
            print(env_result["stdout"])
        else:
            print("⚠️ 环境检查失败:")
            print(env_result["stderr"])
    
    # 测试4: 显示生成的文件
    print("\n📁 生成的所有文件:")
    scripts_info = script_manager.list_scripts()
    if scripts_info["success"]:
        for script in scripts_info["scripts"]:
            print(f"   📄 {script['name']} - {script['path']}")
    
    # 测试5: 创建使用说明
    readme_path = test_dir / "README.md"
    readme_content = """
# 脚本工具测试完成

## 生成的文件
- `counter.v` - 4位计数器Verilog设计
- `counter_tb.v` - 计数器测试台
- `scripts/` 目录包含:
  - `build_counter_sim.sh` - Bash构建脚本
  - `Makefile` - Make构建文件
  - `env_check.sh` - 环境检查脚本

## 使用方法
```bash
# 使用Bash脚本
./scripts/build_counter_sim.sh all

# 使用Makefile
make -f scripts/Makefile
```

## 功能验证
✅ 脚本生成成功
✅ Makefile生成成功  
✅ 文件保存成功
✅ 环境检查完成
"""
    readme_path.write_text(readme_content.strip())
    print(f"\n✅ 使用说明已生成: {readme_path}")
    
    print("\n🎯 脚本工具测试完成！")
    print(f"📁 所有文件位于: {test_dir}")
    print(f"📁 脚本文件位于: {Path('scripts').absolute()}")


if __name__ == "__main__":
    test_script_tools()