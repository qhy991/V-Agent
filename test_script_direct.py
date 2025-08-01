#!/usr/bin/env python3
"""
直接测试脚本工具功能
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.script_tools import ScriptManager


async def main():
    """主测试函数"""
    print("🚀 直接测试脚本工具...")
    
    # 创建脚本管理器实例
    manager = ScriptManager()
    
    # 创建测试目录
    test_dir = Path("script_test_output")
    test_dir.mkdir(exist_ok=True)
    
    # 测试1: 生成bash脚本
    print("📋 测试1: 生成bash构建脚本")
    bash_script = manager.generate_build_script(
        verilog_files=["counter.v"],
        testbench_files=["counter_tb.v"],
        target_name="counter_sim",
        include_wave_generation=True
    )
    
    result = manager.write_script("build_test", bash_script, script_type="bash")
    bash_path = Path(result["script_path"]) if result["success"] else test_dir / "build_test.sh"
    
    print(f"✅ Bash脚本已生成: {bash_path}")
    print("📄 脚本内容预览:")
    print(bash_script[:500] + "..." if len(bash_script) > 500 else bash_script)
    
    # 测试2: 生成Makefile
    print("\n📋 测试2: 生成Makefile")
    makefile_content = manager.generate_makefile(
        verilog_files=["counter.v"],
        testbench_files=["counter_tb.v"],
        target_name="counter_sim",
        top_module="counter"
    )
    
    result = manager.write_script("Makefile", makefile_content, script_type="make")
    makefile_path = Path(result["script_path"]) if result["success"] else test_dir / "Makefile"
    
    print(f"✅ Makefile已生成: {makefile_path}")
    print("📄 Makefile内容预览:")
    print(makefile_content[:500] + "..." if len(makefile_content) > 500 else makefile_content)
    
    # 测试3: 创建简单可执行脚本
    simple_script = """#!/bin/bash
echo "🎯 脚本工具测试成功！"
echo "📁 当前目录: $(pwd)"
echo "🛠️ 脚本执行时间: $(date)"
echo "✅ 所有测试通过！"
"""
    
    test_script_path = test_dir / "test_runner.sh"
    test_script_path.write_text(simple_script)
    test_script_path.chmod(0o755)
    
    # 测试4: 执行脚本
    print("\n⚙️ 测试3: 执行简单脚本")
    result = await manager.execute_script(
        str(test_script_path),
        working_directory=str(test_dir)
    )
    
    if result["success"]:
        print("✅ 脚本执行成功!")
        print("📊 输出:")
        print(result["stdout"])
    else:
        print("❌ 脚本执行失败:")
        print(result["stderr"])
    
    print(f"\n🎯 所有测试文件已保存到: {test_dir}")
    
    # 列出生成的文件
    print("\n📁 生成的文件:")
    for file in test_dir.iterdir():
        print(f"   - {file.name}")


if __name__ == "__main__":
    asyncio.run(main())