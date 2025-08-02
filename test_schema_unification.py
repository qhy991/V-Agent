#!/usr/bin/env python3
"""
测试Schema统一系统
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.schema_system.unified_schemas import UnifiedSchemas, normalize_tool_parameters, resolve_aliases
from core.base_agent import BaseAgent
from core.enums import AgentCapability
from config.config import FrameworkConfig

async def test_unified_schemas():
    """测试统一Schema系统"""
    print("🧪 测试统一Schema系统")
    
    # 测试1: 参数别名解析
    print("\n📋 测试1: 参数别名解析")
    test_params = {
        "code": "module test();",
        "name": "test_module",
        "files": ["test1.v", "test2.v"]
    }
    
    resolved = resolve_aliases(test_params)
    print(f"原始参数: {test_params}")
    print(f"解析后: {resolved}")
    
    expected_mappings = {
        "verilog_code": "module test();",
        "module_name": "test_module", 
        "verilog_files": ["test1.v", "test2.v"]
    }
    
    success = True
    for key, expected_value in expected_mappings.items():
        if resolved.get(key) != expected_value:
            print(f"❌ 映射失败: {key} 期望 {expected_value}, 得到 {resolved.get(key)}")
            success = False
    
    if success:
        print("✅ 参数别名解析测试通过")
    
    # 测试2: 工具Schema获取
    print("\n📋 测试2: 工具Schema获取")
    schema = UnifiedSchemas.get_unified_schema("analyze_code_quality")
    print(f"analyze_code_quality Schema: {schema['type']}")
    print(f"必需参数: {schema.get('required', [])}")
    
    if schema['type'] == 'object' and 'verilog_code' in schema['properties']:
        print("✅ 工具Schema获取测试通过")
    else:
        print("❌ 工具Schema获取测试失败")
    
    # 测试3: 端口定义标准化
    print("\n📋 测试3: 端口定义标准化")
    string_ports = ["clk", "data [7:0]", "enable"]
    normalized_ports = UnifiedSchemas.normalize_port_definitions(string_ports)
    
    print(f"字符串格式: {string_ports}")
    print(f"标准化后: {normalized_ports}")
    
    expected_port = {"name": "data", "width": 8, "description": "data signal (8 bits)"}
    found_data_port = next((p for p in normalized_ports if p["name"] == "data"), None)
    
    if found_data_port and found_data_port["width"] == 8:
        print("✅ 端口定义标准化测试通过")
    else:
        print("❌ 端口定义标准化测试失败")
    
    # 测试4: 完整参数验证和标准化
    print("\n📋 测试4: 完整参数验证和标准化")
    test_params_full = {
        "code": "module adder();",
        "name": "simple_adder",
        "input_ports": ["a [7:0]", "b [7:0]", "cin"],
        "output_ports": ["sum [7:0]", "cout"]
    }
    
    normalized_full = UnifiedSchemas.validate_and_normalize_parameters(
        "generate_verilog_code", test_params_full
    )
    
    print(f"输入参数: {test_params_full}")
    print(f"标准化后: {normalized_full}")
    
    checks = [
        normalized_full.get("verilog_code") == "module adder();",
        normalized_full.get("module_name") == "simple_adder",
        isinstance(normalized_full.get("input_ports"), list),
        len(normalized_full.get("input_ports", [])) == 3
    ]
    
    if all(checks):
        print("✅ 完整参数验证和标准化测试通过")
    else:
        print("❌ 完整参数验证和标准化测试失败")
    
    # 测试5: 映射信息
    print("\n📋 测试5: 参数映射信息")
    mapping_info = UnifiedSchemas.get_parameter_mapping_info()
    print(f"标准参数: {mapping_info['standard_parameters']}")
    print(f"支持的工具: {mapping_info['supported_tools']}")
    print(f"别名映射: {mapping_info['alias_mappings']}")
    
    if len(mapping_info['standard_parameters']) > 5 and len(mapping_info['supported_tools']) > 3:
        print("✅ 参数映射信息测试通过")
    else:
        print("❌ 参数映射信息测试失败")

class TestAgent(BaseAgent):
    """测试智能体"""
    def __init__(self):
        super().__init__(
            agent_id="test_agent",
            role="test",
            capabilities={AgentCapability.CODE_GENERATION}
        )
    
    async def _call_llm_for_function_calling(self, conversation):
        return "Test response"

async def test_base_agent_integration():
    """测试基础智能体集成"""
    print("\n🤖 测试基础智能体集成")
    
    try:
        agent = TestAgent()
        
        # 测试参数标准化方法
        test_params = {
            "code": "module test();",
            "name": "test_module"
        }
        
        normalized = agent._normalize_tool_parameters("test_tool", test_params)
        print(f"智能体参数标准化: {normalized}")
        
        if normalized.get("verilog_code") == "module test();" and normalized.get("module_name") == "test_module":
            print("✅ 基础智能体集成测试通过")
        else:
            print("❌ 基础智能体集成测试失败")
            
    except Exception as e:
        print(f"❌ 基础智能体集成测试异常: {e}")

async def main():
    """主测试函数"""
    print("🎯 开始Schema统一系统测试")
    print("="*60)
    
    await test_unified_schemas()
    await test_base_agent_integration()
    
    print("\n" + "="*60)
    print("🎉 Schema统一系统测试完成")

if __name__ == "__main__":
    asyncio.run(main())