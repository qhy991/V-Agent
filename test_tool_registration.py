#!/usr/bin/env python3
"""
测试工具注册是否正常工作
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig

async def test_tool_registration():
    """测试工具注册是否正常工作"""
    print("🧪 开始测试工具注册...")
    
    # 创建配置
    config = FrameworkConfig.from_env()
    
    # 创建代码审查智能体
    agent = EnhancedRealCodeReviewAgent(config)
    
    # 检查工具是否在增强注册表中
    print(f"\n🔍 检查增强工具注册表:")
    print(f"增强工具数量: {len(agent.enhanced_tools)}")
    print(f"增强工具列表: {list(agent.enhanced_tools.keys())}")
    
    # 检查工具是否在备份注册表中
    print(f"\n🔍 检查备份工具注册表:")
    print(f"备份工具数量: {len(agent._function_registry_backup)}")
    print(f"备份工具列表: {list(agent._function_registry_backup.keys())}")
    
    # 检查generate_testbench工具
    print(f"\n🔍 检查generate_testbench工具:")
    
    # 在增强注册表中
    if "generate_testbench" in agent.enhanced_tools:
        print("✅ generate_testbench 在增强注册表中")
        tool_def = agent.enhanced_tools["generate_testbench"]
        print(f"   函数: {tool_def.func}")
        print(f"   描述: {tool_def.description}")
    else:
        print("❌ generate_testbench 不在增强注册表中")
    
    # 在备份注册表中
    if "generate_testbench" in agent._function_registry_backup:
        print("✅ generate_testbench 在备份注册表中")
        func = agent._function_registry_backup["generate_testbench"]
        print(f"   函数: {func}")
    else:
        print("❌ generate_testbench 不在备份注册表中")
    
    # 测试工具调用
    print(f"\n🧪 测试工具调用:")
    try:
        # 创建测试参数
        test_params = {
            "module_name": "test_counter",
            "module_code": "module test_counter(input clk, output reg [3:0] count); always @(posedge clk) count <= count + 1; endmodule",
            "test_scenarios": [{"name": "basic_test", "description": "基本功能测试"}],
            "clock_period": 10.0,
            "simulation_time": 1000
        }
        
        # 直接调用工具函数
        print("🔧 直接调用 _tool_generate_testbench...")
        result = await agent._tool_generate_testbench(**test_params)
        
        if result.get("success"):
            print("✅ 工具调用成功!")
            print(f"   结果: {result.get('message', 'N/A')}")
        else:
            print("❌ 工具调用失败!")
            print(f"   错误: {result.get('error', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 工具调用异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ 工具注册测试完成")

if __name__ == "__main__":
    asyncio.run(test_tool_registration()) 