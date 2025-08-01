#!/usr/bin/env python3
"""
正确执行LLM生成的脚本
"""

import asyncio
import sys
from pathlib import Path
import subprocess

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.script_tools import ScriptManager


def test_makefile_execution():
    """测试Makefile执行"""
    print("🔧 测试Makefile执行")
    
    # 使用最新的实验目录
    latest_exp = Path("logs/experiment_20250731_155750")
    artifacts_dir = latest_exp / "artifacts"
    makefile_path = artifacts_dir / "scripts" / "simulation.mk"
    
    if not makefile_path.exists():
        print("❌ 没有找到Makefile")
        return False
    
    print(f"📁 使用Makefile: {makefile_path}")
    
    # 读取Makefile内容
    content = makefile_path.read_text()
    print("📄 Makefile内容:")
    print("=" * 50)
    print(content)
    print("=" * 50)
    
    # 创建工作目录和测试文件
    work_dir = Path("script_execution_test")
    work_dir.mkdir(exist_ok=True)
    
    # 复制相关文件
    design_src = artifacts_dir / "complex_design.v"
    tb_src = artifacts_dir / "unknown_module_tb.v"
    
    if design_src.exists():
        design_dst = work_dir / "complex_design.v"
        design_dst.write_text(design_src.read_text())
        print(f"✅ 复制设计文件: {design_dst}")
    
    if tb_src.exists():
        tb_dst = work_dir / "unknown_module_tb.v"
        tb_dst.write_text(tb_src.read_text())
        print(f"✅ 复制测试台: {tb_dst}")
    
    # 复制Makefile
    makefile_dst = work_dir / "Makefile"
    makefile_dst.write_text(content)
    print(f"✅ 复制Makefile: {makefile_dst}")
    
    # 测试Makefile
    print("\n⚙️ 测试Makefile...")
    
    try:
        # 干运行测试
        result = subprocess.run(
            ["make", "--dry-run"],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"📊 干运行返回码: {result.returncode}")
        if result.stdout:
            print("📋 干运行输出:")
            print(result.stdout)
        if result.stderr:
            print("⚠️  干运行警告:")
            print(result.stderr)
            
        # 如果干运行成功，尝试构建
        if result.returncode == 0:
            print("\n🚀 执行实际构建...")
            build_result = subprocess.run(
                ["make"],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(f"📊 构建返回码: {build_result.returncode}")
            if build_result.stdout:
                print("✅ 构建输出:")
                print(build_result.stdout)
            if build_result.stderr:
                print("📋 构建信息:")
                print(build_result.stderr)
                
            return build_result.returncode == 0
            
    except subprocess.TimeoutExpired:
        print("⏰ 构建超时")
    except FileNotFoundError:
        print("⚠️  make命令未找到")
    except Exception as e:
        print(f"❌ 执行错误: {e}")
    
    return False


def test_bash_script_execution():
    """测试Bash脚本执行"""
    print("\n🐚 测试Bash脚本执行")
    
    # 创建简单的Bash脚本
    work_dir = Path("bash_test")
    work_dir.mkdir(exist_ok=True)
    
    # 创建简单Verilog文件
    test_v = work_dir / "test.v"
    test_v.write_text('''
module test();
    initial begin
        $display("Hello from Verilog simulation!");
        $display("Current time: %t", $time);
        #10 $finish;
    end
endmodule
''')
    
    # 创建Bash脚本
    script_manager = ScriptManager()
    bash_script = script_manager.generate_build_script(
        verilog_files=[str(test_v)],
        testbench_files=[],
        target_name="test_sim",
        include_wave_generation=False
    )
    
    script_result = script_manager.write_script(
        "test_build",
        bash_script,
        script_type="bash"
    )
    
    if script_result["success"]:
        script_path = Path(script_result["script_path"])
        print(f"📁 生成脚本: {script_path}")
        
        # 复制到工作目录
        work_script = work_dir / "build_test.sh"
        work_script.write_text(script_path.read_text())
        
        # 执行脚本
        print("\n⚙️ 执行Bash脚本...")
        result = script_manager.execute_script(
            str(work_script),
            working_directory=str(work_dir)
        )
        
        if result["success"]:
            print("✅ Bash脚本执行成功!")
            print("📊 执行输出:")
            print(result["stdout"])
            return True
        else:
            print("❌ Bash脚本执行失败:")
            print(result["stderr"])
    
    return False


def main():
    """主函数"""
    print("🎯 LLM生成脚本执行验证")
    print("=" * 50)
    
    # 测试Makefile执行
    makefile_success = test_makefile_execution()
    
    # 测试Bash脚本执行
    bash_success = test_bash_script_execution()
    
    print("\n" + "=" * 50)
    print("📊 最终执行结果:")
    print(f"   Makefile执行: {'✅ 成功' if makefile_success else '❌ 失败'}")
    print(f"   Bash脚本执行: {'✅ 成功' if bash_success else '❌ 失败'}")
    
    if makefile_success or bash_success:
        print("\n🎉 LLM生成的脚本已成功执行!")
    else:
        print("\n⚠️  需要检查iverilog安装和脚本内容")


if __name__ == "__main__":
    main()