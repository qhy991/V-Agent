#!/usr/bin/env python3
"""
快速脚本工具测试
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from tools.script_tools import ScriptManager


async def test_script_tools():
    """测试脚本工具"""
    print("🚀 测试脚本工具...")
    
    # 初始化脚本管理器
    script_manager = ScriptManager()
    
    # 创建测试目录
    test_dir = Path("quick_test")
    test_dir.mkdir(exist_ok=True)
    
    # 测试1: 创建简单脚本
    script_content = """#!/bin/bash
echo "Hello from script tool!"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la
echo "Script executed successfully!"
"""
    
    script_path = test_dir / "test_script.sh"
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    print(f"📁 脚本已创建: {script_path}")
    
    # 测试2: 执行脚本
    result = await script_manager.execute_script(
        str(script_path),
        working_directory=str(test_dir)
    )
    
    if result["success"]:
        print("✅ 脚本执行成功!")
        print("📊 输出:")
        print(result["stdout"])
    else:
        print("❌ 脚本执行失败:")
        print(result["stderr"])
    
    # 测试3: 生成Makefile
    from tools.script_tools import ScriptManager
    
    verilog_files = ["design.v"]
    testbench_files = ["design_tb.v"]
    
    makefile_content = script_manager.generate_makefile_content(
        verilog_files=verilog_files,
        testbench_files=testbench_files,
        target_name="design_sim",
        top_module="design"
    )
    
    makefile_path = test_dir / "Makefile"
    makefile_path.write_text(makefile_content)
    
    print(f"📋 Makefile已创建: {makefile_path}")
    print("📄 Makefile内容:")
    print(makefile_content)
    
    print(f"\n✅ 测试完成！文件保存在: {test_dir}")


if __name__ == "__main__":
    asyncio.run(test_script_tools())