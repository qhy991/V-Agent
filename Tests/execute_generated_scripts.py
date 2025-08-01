#!/usr/bin/env python3
"""
执行LLM生成的脚本，验证完整流程
"""

import asyncio
import sys
from pathlib import Path
import time

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.script_tools import ScriptManager


async def execute_llm_generated_scripts():
    """执行LLM生成的脚本"""
    print("🚀 执行LLM生成的脚本测试")
    print("=" * 50)
    
    # 找到最新的实验目录
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("❌ 没有找到logs目录")
        return
    
    # 找到最新的实验目录
    experiment_dirs = [d for d in logs_dir.iterdir() if d.is_dir() and d.name.startswith("experiment_")]
    if not experiment_dirs:
        print("❌ 没有找到实验目录")
        return
    
    latest_experiment = max(experiment_dirs, key=lambda x: x.stat().st_mtime)
    print(f"📁 使用实验目录: {latest_experiment}")
    
    # 查找生成的脚本
    scripts_dir = latest_experiment / "artifacts" / "scripts"
    if not scripts_dir.exists():
        print("❌ 没有找到scripts目录")
        return
    
    # 列出所有生成的脚本
    generated_scripts = list(scripts_dir.glob("*.sh")) + list(scripts_dir.glob("*.mk"))
    print(f"📋 找到 {len(generated_scripts)} 个生成的脚本:")
    for script in generated_scripts:
        print(f"   📄 {script.name}")
    
    # 执行Bash脚本
    bash_scripts = list(scripts_dir.glob("*.sh"))
    if bash_scripts:
        print(f"\n⚙️ 执行Bash脚本...")
        script_manager = ScriptManager()
        
        for bash_script in bash_scripts:
            print(f"\n🎯 执行: {bash_script.name}")
            
            # 检查脚本内容
            content = bash_script.read_text()
            print(f"📄 脚本长度: {len(content)} 字符")
            print(f"📄 预览: {content[:200]}...")
            
            # 执行脚本
            result = script_manager.execute_script(
                str(bash_script),
                working_directory=str(scripts_dir.parent)
            )
            
            if result["success"]:
                print("✅ 执行成功!")
                print("📊 输出:")
                print(result["stdout"])
            else:
                print("❌ 执行失败:")
                print(result["stderr"])
    
    # 测试Makefile
    makefiles = list(scripts_dir.glob("*.mk")) + list(scripts_dir.glob("Makefile"))
    if makefiles:
        print(f"\n🔧 测试Makefile...")
        
        for makefile in makefiles:
            print(f"\n🎯 测试: {makefile.name}")
            
            # 检查Makefile内容
            content = makefile.read_text()
            print(f"📄 Makefile长度: {len(content)} 字符")
            print(f"📄 预览: {content[:200]}...")
            
            # 创建测试文件用于make
            test_dir = scripts_dir.parent
            test_v = test_dir / "test.v"
            test_v.write_text('''
module test();
    initial begin
        $display("Hello from test module!");
        $finish;
    end
endmodule
''')
            
            # 使用make命令测试
            try:
                import subprocess
                result = subprocess.run(
                    ["make", "-f", str(makefile.name), "--dry-run"],
                    cwd=str(test_dir),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print("✅ Makefile语法正确!")
                    print("📊 干运行结果:")
                    print(result.stdout)
                else:
                    print("❌ Makefile错误:")
                    print(result.stderr)
                    
            except subprocess.TimeoutExpired:
                print("⏰ Makefile测试超时")
            except FileNotFoundError:
                print("⚠️  make命令未找到，跳过Makefile测试")
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 执行总结:")
    print(f"   找到脚本: {len(generated_scripts)} 个")
    print(f"   Bash脚本: {len(bash_scripts)} 个")
    print(f"   Makefile: {len(makefiles)} 个")
    
    # 显示生成的文件结构
    print(f"\n📁 完整文件结构:")
    for item in latest_experiment.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(latest_experiment)
            print(f"   📄 {rel_path}")


if __name__ == "__main__":
    asyncio.run(execute_llm_generated_scripts())