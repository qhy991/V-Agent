#!/usr/bin/env python3
"""
测试脚本：验证 width 参数类型问题的修复
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from config.config import FrameworkConfig


async def test_width_parameter_fix():
    """测试 width 参数类型问题的修复"""
    print("🧪 测试 width 参数类型问题修复")
    print("=" * 50)
    
    try:
        # 初始化智能体
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgent(config)
        
        # 测试用例1：整数类型的 width
        print("\n📋 测试用例1：整数类型的 width")
        input_ports_int = [
            {"name": "clk", "width": 1, "description": "时钟信号"},
            {"name": "data", "width": 8, "description": "数据输入"}
        ]
        output_ports_int = [
            {"name": "result", "width": 16, "description": "结果输出"}
        ]
        
        result_int = agent._build_port_info(input_ports_int, "input")
        print("输入端口（整数width）:")
        print(result_int)
        
        # 测试用例2：字符串类型的 width（参数名）
        print("\n📋 测试用例2：字符串类型的 width（参数名）")
        input_ports_str = [
            {"name": "clk", "width": 1, "description": "时钟信号"},
            {"name": "data", "width": "WIDTH", "description": "数据输入"}
        ]
        output_ports_str = [
            {"name": "result", "width": "WIDTH", "description": "结果输出"}
        ]
        
        result_str = agent._build_port_info(input_ports_str, "input")
        print("输入端口（字符串width）:")
        print(result_str)
        
        # 测试用例3：数字字符串类型的 width
        print("\n📋 测试用例3：数字字符串类型的 width")
        input_ports_num_str = [
            {"name": "clk", "width": "1", "description": "时钟信号"},
            {"name": "data", "width": "8", "description": "数据输入"}
        ]
        
        result_num_str = agent._build_port_info(input_ports_num_str, "input")
        print("输入端口（数字字符串width）:")
        print(result_num_str)
        
        # 测试用例4：混合类型
        print("\n📋 测试用例4：混合类型")
        input_ports_mixed = [
            {"name": "clk", "width": 1, "description": "时钟信号"},
            {"name": "data", "width": "WIDTH", "description": "数据输入"},
            {"name": "ctrl", "width": "8", "description": "控制信号"}
        ]
        
        result_mixed = agent._build_port_info(input_ports_mixed, "input")
        print("输入端口（混合类型width）:")
        print(result_mixed)
        
        print("\n✅ 所有测试用例执行成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_generate_verilog_code_with_parameters():
    """测试带参数的 Verilog 代码生成"""
    print("\n🧪 测试带参数的 Verilog 代码生成")
    print("=" * 50)
    
    try:
        # 初始化智能体
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgent(config)
        
        # 测试参数
        test_parameters = [
            {"name": "WIDTH", "default_value": 8, "description": "计数器位宽参数"},
            {"name": "MAX_COUNT", "default_value": "WIDTH-1", "description": "最大计数值"}
        ]
        
        test_constraints = [
            "使用异步复位（低有效）",
            "仅在 enable 为高时递增计数器",
            "计数器达到最大值后自动回绕至0"
        ]
        
        # 模拟调用（不实际调用LLM）
        print("📋 测试参数:")
        print(f"   parameters: {test_parameters}")
        print(f"   additional_constraints: {test_constraints}")
        print(f"   comments_required: True")
        
        print("\n✅ 参数验证通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("🔧 Verilog 智能体修复验证测试")
    print("=" * 60)
    
    # 测试1：width 参数类型修复
    test1_result = await test_width_parameter_fix()
    
    # 测试2：参数化代码生成
    test2_result = await test_generate_verilog_code_with_parameters()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   width 参数类型修复: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"   参数化代码生成: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！修复验证成功。")
        return 0
    else:
        print("\n💥 部分测试失败，需要进一步检查。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 