#!/usr/bin/env python3
"""
测试仿真工作目录修复效果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

async def test_simulation_working_directory():
    """测试仿真工作目录修复效果"""
    print("🧪 测试仿真工作目录修复效果")
    print("=" * 60)
    
    # 创建代理实例
    config = FrameworkConfig.from_env()
    agent = EnhancedRealCodeReviewAgent(config)
    
    print(f"📁 当前工作目录: {Path.cwd()}")
    print(f"📁 项目根目录: {project_root}")
    
    # 检查文件是否存在
    module_file = "file_workspace/designs/adder_16bit.v"
    testbench_file = "file_workspace/testbenches/adder_16bit_tb_14.v"
    
    print(f"\n📋 文件检查:")
    print(f"   模块文件: {module_file} - {'✅ 存在' if Path(module_file).exists() else '❌ 不存在'}")
    print(f"   测试台文件: {testbench_file} - {'✅ 存在' if Path(testbench_file).exists() else '❌ 不存在'}")
    
    if not Path(module_file).exists():
        print("❌ 模块文件不存在，无法进行仿真测试")
        return
    
    if not Path(testbench_file).exists():
        print("❌ 测试台文件不存在，无法进行仿真测试")
        return
    
    print(f"\n🔬 开始仿真测试...")
    
    try:
        # 调用仿真工具
        result = await agent._tool_run_simulation(
            module_file=module_file,
            testbench_file=testbench_file,
            simulator="iverilog"
        )
        
        print(f"\n📊 仿真结果:")
        print(f"   成功: {result.get('success', False)}")
        
        if result.get('success', False):
            print("✅ 仿真执行成功！")
            print(f"   输出文件: {result.get('waveform_file', 'N/A')}")
            print(f"   返回码: {result.get('return_code', 'N/A')}")
            
            # 显示仿真输出
            output = result.get('output', '')
            if output:
                print(f"\n📋 仿真输出:")
                print("-" * 40)
                print(output[:500] + "..." if len(output) > 500 else output)
        else:
            print("❌ 仿真执行失败！")
            error = result.get('error', 'Unknown error')
            print(f"   错误: {error}")
            
            # 显示编译输出
            compilation_output = result.get('compilation_output', '')
            if compilation_output:
                print(f"\n📋 编译输出:")
                print("-" * 40)
                print(compilation_output)
            
            # 显示命令
            command = result.get('command', '')
            if command:
                print(f"\n🔧 执行的命令: {command}")
                
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ 工作目录修复测试完成！")

if __name__ == "__main__":
    asyncio.run(test_simulation_working_directory()) 