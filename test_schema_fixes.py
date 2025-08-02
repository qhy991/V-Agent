#!/usr/bin/env python3
"""
测试Schema修复效果 - 验证AI Agent与工具Schema不匹配问题的修复
"""

import sys
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.schema_system.flexible_schema_adapter import FlexibleSchemaAdapter
from core.schema_system.field_mapper import FieldMapper
from core.schema_system.parameter_repairer import ParameterRepairer
from core.schema_system.schema_validator import SchemaValidator

def setup_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_schema_fixes.log')
        ]
    )

def get_test_verilog_schema() -> Dict[str, Any]:
    """获取generate_verilog_code工具的测试Schema"""
    return {
        "type": "object",
        "properties": {
            "module_name": {
                "type": "string",
                "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                "minLength": 1,
                "maxLength": 100,
                "description": "Verilog模块名称"
            },
            "requirements": {
                "type": "string",
                "minLength": 10,
                "maxLength": 10000,
                "description": "设计需求和功能描述"
            },
            "input_ports": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                            "maxLength": 50
                        },
                        "width": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1024,
                            "default": 1
                        },
                        "description": {
                            "type": "string",
                            "maxLength": 200
                        }
                    },
                    "required": ["name"],
                    "additionalProperties": False
                },
                "maxItems": 100,
                "description": "输入端口定义列表"
            },
            "output_ports": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                            "maxLength": 50
                        },
                        "width": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1024,
                            "default": 1
                        },
                        "description": {
                            "type": "string",
                            "maxLength": 200
                        }
                    },
                    "required": ["name"],
                    "additionalProperties": False
                },
                "maxItems": 100,
                "description": "输出端口定义列表"
            },
            "coding_style": {
                "type": "string",
                "enum": ["behavioral", "structural", "rtl", "mixed"],
                "default": "rtl",
                "description": "Verilog编码风格"
            }
        },
        "required": ["module_name", "requirements"],
        "additionalProperties": False
    }

def get_test_problematic_parameters() -> Dict[str, Any]:
    """获取模拟AI Agent输出的问题参数（基于test-12.log）"""
    return {
        # 问题1: 端口定义为字符串数组而不是对象数组
        "input_ports": ["a [7:0]", "b [7:0]", "cin"],
        "output_ports": ["sum [7:0]", "cout"],
        
        # 问题2: 缺少必需字段
        # "module_name": "simple_8bit_adder",  # 故意缺少
        "requirements": "设计一个8位加法器，支持基本的二进制加法运算",
        
        # 问题3: 错误的字段名
        "verilog_code": "// some code here",  # 应该没有这个字段
        
        # 问题4: 额外的不允许字段
        "design_files": ["adder.v"],
        "target_platform": "FPGA",
        "optimization_level": "high"
    }

def get_test_code_analysis_schema() -> Dict[str, Any]:
    """获取analyze_code_quality工具的测试Schema"""
    return {
        "type": "object",
        "properties": {
            "verilog_code": {
                "type": "string",
                "minLength": 10,
                "maxLength": 100000,
                "description": "待分析的Verilog代码"
            },
            "analysis_scope": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["syntax", "style", "timing", "synthesis", "simulation", "coverage"]
                },
                "default": ["syntax", "style"],
                "description": "分析范围选择"
            },
            "coding_standard": {
                "type": "string",
                "enum": ["ieee1800", "custom", "industry"],
                "default": "ieee1800",
                "description": "编码标准规范"
            }
        },
        "required": ["verilog_code"],
        "additionalProperties": False
    }

def get_test_code_analysis_parameters() -> Dict[str, Any]:
    """获取代码分析的问题参数"""
    return {
        # 问题: 字段名不匹配
        "code": "module test(); endmodule",  # 应该是verilog_code
        "scope": ["syntax", "style"],       # 应该是analysis_scope
        "standard": "ieee1800"              # 应该是coding_standard
    }

def test_field_mapper():
    """测试字段映射器"""
    print("🔧 测试字段映射器")
    print("=" * 50)
    
    mapper = FieldMapper()
    
    # 测试1: generate_verilog_code工具
    print("\n📋 测试1: generate_verilog_code字段映射")
    schema = get_test_verilog_schema()
    problematic_data = get_test_problematic_parameters()
    
    print(f"原始参数: {json.dumps(problematic_data, indent=2, ensure_ascii=False)}")
    
    mapped_data = mapper.map_fields(problematic_data, "generate_verilog_code", schema)
    print(f"映射后参数: {json.dumps(mapped_data, indent=2, ensure_ascii=False)}")
    
    # 测试2: analyze_code_quality工具
    print("\n📋 测试2: analyze_code_quality字段映射")
    analysis_schema = get_test_code_analysis_schema()
    analysis_data = get_test_code_analysis_parameters()
    
    print(f"原始参数: {json.dumps(analysis_data, indent=2, ensure_ascii=False)}")
    
    mapped_analysis = mapper.map_fields(analysis_data, "analyze_code_quality", analysis_schema)
    print(f"映射后参数: {json.dumps(mapped_analysis, indent=2, ensure_ascii=False)}")

def test_schema_adapter():
    """测试Schema适配器"""
    print("\n\n🔄 测试Schema适配器")
    print("=" * 50)
    
    adapter = FlexibleSchemaAdapter()
    
    # 测试完整的适配流程
    print("\n📋 测试完整适配流程")
    schema = get_test_verilog_schema()
    problematic_data = get_test_problematic_parameters()
    
    print(f"原始参数: {json.dumps(problematic_data, indent=2, ensure_ascii=False)}")
    
    adaptation_result = adapter.adapt_parameters(problematic_data, schema, "generate_verilog_code")
    
    print(f"\n适配结果:")
    print(f"  成功: {adaptation_result.success}")
    print(f"  转换: {adaptation_result.transformations}")
    print(f"  警告: {adaptation_result.warnings}")
    
    if adaptation_result.adapted_data:
        print(f"\n适配后参数: {json.dumps(adaptation_result.adapted_data, indent=2, ensure_ascii=False)}")

def test_schema_validation():
    """测试Schema验证"""
    print("\n\n✅ 测试Schema验证")
    print("=" * 50)
    
    validator = SchemaValidator()
    adapter = FlexibleSchemaAdapter()
    
    schema = get_test_verilog_schema()
    problematic_data = get_test_problematic_parameters()
    
    # 1. 验证原始数据（应该失败）
    print("\n📋 验证原始问题数据:")
    original_result = validator.validate(problematic_data, schema)
    print(f"验证结果: {'通过' if original_result.is_valid else '失败'}")
    if not original_result.is_valid:
        print(f"错误数量: {len(original_result.errors)}")
        for i, error in enumerate(original_result.errors[:3], 1):  # 只显示前3个错误
            print(f"  {i}. {error.field_path}: {error.message}")
    
    # 2. 验证适配后的数据（应该成功）
    print("\n📋 验证适配后数据:")
    adaptation_result = adapter.adapt_parameters(problematic_data, schema, "generate_verilog_code")
    
    if adaptation_result.success and adaptation_result.adapted_data:
        adapted_validation = validator.validate(adaptation_result.adapted_data, schema)
        print(f"验证结果: {'通过' if adapted_validation.is_valid else '失败'}")
        
        if not adapted_validation.is_valid:
            print(f"剩余错误数量: {len(adapted_validation.errors)}")
            for i, error in enumerate(adapted_validation.errors, 1):
                print(f"  {i}. {error.field_path}: {error.message}")
        else:
            print("🎉 适配成功！所有参数现在都符合Schema要求")

def test_port_conversion():
    """测试端口转换功能"""
    print("\n\n🔌 测试端口转换功能")
    print("=" * 50)
    
    adapter = FlexibleSchemaAdapter()
    
    # 测试各种端口格式
    test_cases = [
        ["a [7:0]", "b [7:0]", "cin"],
        ["clk", "rst", "data [15:0]", "valid"],
        ["input [31:0]", "output [7:0]"]
    ]
    
    for i, port_strings in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {port_strings}")
        
        port_objects = adapter._convert_port_strings_to_objects(port_strings)
        if port_objects:
            print("转换结果:")
            for port in port_objects:
                print(f"  - {port['name']}: {port['width']} bits ({port['description']})")
        else:
            print("  转换失败")

def test_end_to_end_scenario():
    """端到端场景测试"""
    print("\n\n🚀 端到端场景测试")
    print("=" * 50)
    
    print("模拟test-12.log中的实际问题场景:")
    
    # 模拟AI Agent的实际输出（基于test-12.log）
    ai_agent_output = {
        "input_ports": ["a [7:0]", "b [7:0]", "cin"],
        "output_ports": ["sum [7:0]", "cout"],
        "requirements": "设计一个简单的8位加法器，支持基本的二进制加法运算。",
        # 缺少module_name
        "verilog_code": "// some generated code",  # 错误字段名
        "design_files": ["adder.v"],  # 额外字段
        "target_platform": "FPGA"     # 额外字段
    }
    
    print(f"AI Agent输出: {json.dumps(ai_agent_output, indent=2, ensure_ascii=False)}")
    
    # 完整的修复流程
    adapter = FlexibleSchemaAdapter()
    validator = SchemaValidator()
    schema = get_test_verilog_schema()
    
    # 1. 尝试直接验证（应该失败）
    print("\n1️⃣ 直接验证（预期失败）:")
    direct_validation = validator.validate(ai_agent_output, schema)
    print(f"结果: {'通过' if direct_validation.is_valid else '失败'} ({len(direct_validation.errors)} 个错误)")
    
    # 2. 智能适配
    print("\n2️⃣ 应用智能适配:")
    adaptation_result = adapter.adapt_parameters(ai_agent_output, schema, "generate_verilog_code")
    print(f"适配成功: {adaptation_result.success}")
    print(f"应用的转换: {adaptation_result.transformations}")
    
    # 3. 验证适配后的结果
    print("\n3️⃣ 验证适配后结果:")
    if adaptation_result.success and adaptation_result.adapted_data:
        final_validation = validator.validate(adaptation_result.adapted_data, schema)
        print(f"最终验证: {'通过' if final_validation.is_valid else '失败'}")
        
        if final_validation.is_valid:
            print("🎉 成功！Schema不匹配问题已解决")
            print(f"最终参数: {json.dumps(adaptation_result.adapted_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"仍有 {len(final_validation.errors)} 个错误需要处理:")
            for error in final_validation.errors:
                print(f"  - {error.field_path}: {error.message}")

def main():
    """主测试函数"""
    print("🧪 Schema修复效果验证测试")
    print("=" * 80)
    
    setup_logging()
    
    try:
        # 运行各项测试
        test_field_mapper()
        test_schema_adapter()
        test_schema_validation()
        test_port_conversion()
        test_end_to_end_scenario()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！请查看输出确认Schema修复是否生效")
        print("📄 详细日志已保存到: test_schema_fixes.log")
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()