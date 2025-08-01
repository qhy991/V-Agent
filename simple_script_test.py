#!/usr/bin/env python3
"""
简化版脚本工具测试程序
快速验证agent的脚本工具功能
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from agents.real_code_reviewer import RealCodeReviewAgent
from tools.script_tools import ScriptManager


async def simple_script_test():
    """简化版脚本测试"""
    print("🔧 开始简化版脚本工具测试...")
    
    # 初始化配置
    config = FrameworkConfig.from_env()
    
    # 创建测试目录
    test_dir = Path("test_script_output")
    test_dir.mkdir(exist_ok=True)
    
    # 创建简单的测试文件
    test_file = test_dir / "hello.v"
    test_file.write_text('''
module hello_world();
    initial begin
        $display("Hello from Verilog!");
        $finish;
    end
endmodule
''')
    
    # 创建智能体实例
    reviewer = RealCodeReviewAgent(config)
    
    # 测试1: 生成构建脚本
    print("📋 测试1: 生成构建脚本...")
    result = await reviewer._tool_write_build_script(
        verilog_files=[str(test_file)],
        testbench_files=[],
        target_name="hello_test",
        script_type="bash"
    )
    
    if result["success"]:
        script_path = result["result"]["script_path"]
        print(f"✅ 脚本生成成功: {script_path}")
        
        # 测试2: 执行脚本
        print("⚙️ 测试2: 执行脚本...")
        script_manager = ScriptManager()
        
        exec_result = await script_manager.execute_script(
            script_path,
            working_directory=str(test_dir)
        )
        
        if exec_result["success"]:
            print("✅ 脚本执行成功!")
            print("📊 输出:")
            print(exec_result["stdout"])
        else:
            print("❌ 脚本执行失败:")
            print(exec_result["stderr"])
    else:
        print("❌ 脚本生成失败:")
        print(result["error"])

    print(f"📁 测试文件保存在: {test_dir}")


if __name__ == "__main__":
    asyncio.run(simple_script_test())