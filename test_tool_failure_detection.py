#!/usr/bin/env python3
"""
测试工具失败检测修复效果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

async def test_tool_failure_detection():
    """测试工具失败检测功能"""
    print("🧪 测试工具失败检测修复效果")
    print("=" * 60)
    
    # 创建代理实例
    config = FrameworkConfig.from_env()
    agent = EnhancedRealCodeReviewAgent(config)
    
    print("📝 测试仿真工具失败检测...")
    
    try:
        # 调用仿真工具，使用一个有语法错误的测试台文件
        result = await agent._tool_run_simulation(
            module_file="file_workspace/designs/adder_16bit.v",
            testbench_file="file_workspace/testbenches/adder_16bit_tb.v",  # 这个文件有语法错误
            simulator="iverilog"
        )
        
        print(f"\n📊 仿真结果:")
        print(f"   成功: {result.get('success', False)}")
        print(f"   错误: {result.get('error', 'None')}")
        print(f"   阶段: {result.get('stage', 'Unknown')}")
        
        if result.get('success', False):
            print("✅ 仿真成功（这不应该发生，因为测试台有语法错误）")
        else:
            print("❌ 仿真失败（这是预期的，因为测试台有语法错误）")
            
            # 显示编译错误
            compilation_output = result.get('compilation_output', '')
            if compilation_output:
                print(f"\n📋 编译错误:")
                print("-" * 40)
                print(compilation_output)
        
        # 测试工具调用的处理
        print(f"\n🔍 测试工具调用处理...")
        
        # 模拟一个工具调用
        from core.function_calling import ToolCall
        
        tool_call = ToolCall(
            tool_name="run_simulation",
            parameters={
                "module_file": "file_workspace/designs/adder_16bit.v",
                "testbench_file": "file_workspace/testbenches/adder_16bit_tb.v"
            },
            call_id="test_call_1"
        )
        
        # 执行工具调用
        tool_result = await agent._execute_enhanced_tool_call(tool_call)
        
        print(f"   工具调用成功: {tool_result.success}")
        print(f"   工具调用错误: {tool_result.error}")
        
        if not tool_result.success:
            print("✅ 工具失败被正确检测到")
        else:
            print("❌ 工具失败没有被检测到")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ 工具失败检测测试完成！")

if __name__ == "__main__":
    asyncio.run(test_tool_failure_detection()) 