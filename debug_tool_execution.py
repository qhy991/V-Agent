#!/usr/bin/env python3
"""
工具执行诊断脚本
用于排查工具执行引擎的路由逻辑问题
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.function_calling import ToolCall, ToolResult
from core.schema_system.unified_schemas import UnifiedSchemas
from core.schema_system.flexible_schema_adapter import FlexibleSchemaAdapter
from core.schema_system.schema_validator import SchemaValidator
from core.schema_system.parameter_repairer import ParameterRepairer

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ToolExecutionDiagnostic:
    """工具执行诊断器"""
    
    def __init__(self):
        self.schema_adapter = FlexibleSchemaAdapter()
        self.schema_validator = SchemaValidator()
        self.parameter_repairer = ParameterRepairer()
        
    async def test_unified_schemas(self):
        """测试统一Schema系统"""
        logger.info("🔍 测试统一Schema系统...")
        
        try:
            # 测试参数标准化
            test_params = {
                "module_name": "counter",
                "verilog_code": "module counter(...); endmodule",
                "test_scenarios": ["test1", "test2"]
            }
            
            normalized = UnifiedSchemas.validate_and_normalize_parameters(
                "generate_testbench", test_params
            )
            logger.info(f"✅ 参数标准化成功: {normalized}")
            
        except Exception as e:
            logger.error(f"❌ 参数标准化失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def test_schema_adapter(self):
        """测试Schema适配器"""
        logger.info("🔍 测试Schema适配器...")
        
        try:
            test_params = {
                "module_name": "counter",
                "verilog_code": "module counter(...); endmodule",
                "test_scenarios": ["test1", "test2"]
            }
            
            schema = {
                "type": "object",
                "properties": {
                    "module_name": {"type": "string"},
                    "verilog_code": {"type": "string"},
                    "test_scenarios": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["module_name", "verilog_code"]
            }
            
            result = self.schema_adapter.adapt_parameters(
                test_params, schema, "generate_testbench"
            )
            
            if result.success:
                logger.info(f"✅ Schema适配成功: {result.adapted_data}")
                logger.info(f"   转换: {result.transformations}")
            else:
                logger.error(f"❌ Schema适配失败: {result.warnings}")
                
        except Exception as e:
            logger.error(f"❌ Schema适配器测试失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def test_schema_validator(self):
        """测试Schema验证器"""
        logger.info("🔍 测试Schema验证器...")
        
        try:
            test_params = {
                "module_name": "counter",
                "verilog_code": "module counter(...); endmodule",
                "test_scenarios": ["test1", "test2"]
            }
            
            schema = {
                "type": "object",
                "properties": {
                    "module_name": {"type": "string"},
                    "verilog_code": {"type": "string"},
                    "test_scenarios": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["module_name", "verilog_code"]
            }
            
            result = self.schema_validator.validate(test_params, schema)
            
            if result.is_valid:
                logger.info("✅ Schema验证通过")
            else:
                logger.error(f"❌ Schema验证失败: {result.get_error_summary()}")
                
        except Exception as e:
            logger.error(f"❌ Schema验证器测试失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def test_parameter_repairer(self):
        """测试参数修复器"""
        logger.info("🔍 测试参数修复器...")
        
        try:
            # 创建无效的参数
            invalid_params = {
                "module_name": 123,  # 应该是字符串
                "verilog_code": None,  # 应该是字符串
                "test_scenarios": "not_an_array"  # 应该是数组
            }
            
            schema = {
                "type": "object",
                "properties": {
                    "module_name": {"type": "string"},
                    "verilog_code": {"type": "string"},
                    "test_scenarios": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["module_name", "verilog_code"]
            }
            
            # 先验证参数
            validation_result = self.schema_validator.validate(invalid_params, schema)
            logger.info(f"验证结果: {validation_result.get_error_summary()}")
            
            # 尝试修复参数
            repair_result = self.parameter_repairer.repair_parameters(
                invalid_params, schema, validation_result
            )
            
            if repair_result.success:
                logger.info(f"✅ 参数修复成功: {repair_result.repaired_data}")
                logger.info(f"   修复建议: {[s.to_dict() for s in repair_result.suggestions]}")
            else:
                logger.warning(f"⚠️ 参数修复失败: {repair_result.suggestions}")
                
        except Exception as e:
            logger.error(f"❌ 参数修复器测试失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def test_field_mapper(self):
        """测试字段映射器"""
        logger.info("🔍 测试字段映射器...")
        
        try:
            from core.schema_system.field_mapper import FieldMapper
            
            field_mapper = FieldMapper()
            
            # 测试字段映射
            test_data = {
                "code": "module counter(...); endmodule",  # 应该映射到 verilog_code
                "test_cases": ["test1", "test2"],  # 应该映射到 test_scenarios
                "name": "counter"  # 应该映射到 module_name
            }
            
            schema = {
                "type": "object",
                "properties": {
                    "module_name": {"type": "string"},
                    "verilog_code": {"type": "string"},
                    "test_scenarios": {"type": "array", "items": {"type": "string"}}
                }
            }
            
            mapped_data = field_mapper.map_fields(test_data, "generate_testbench", schema)
            logger.info(f"✅ 字段映射成功: {mapped_data}")
            
        except Exception as e:
            logger.error(f"❌ 字段映射器测试失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def test_tool_registry_integration(self):
        """测试工具注册表集成"""
        logger.info("🔍 测试工具注册表集成...")
        
        try:
            # 检查工具注册表
            from core.enhanced_tool_registry import EnhancedToolRegistry
            
            registry = EnhancedToolRegistry()
            
            # 模拟工具函数
            def mock_generate_testbench(module_name: str, verilog_code: str, test_scenarios: list = None):
                return {
                    "success": True,
                    "testbench_code": f"// Testbench for {module_name}\nmodule {module_name}_tb;\n// ...",
                    "message": "Testbench generated successfully"
                }
            
            # 注册工具
            registry.register_tool(
                name="generate_testbench",
                func=mock_generate_testbench,
                description="Generate testbench for Verilog module",
                schema={
                    "type": "object",
                    "properties": {
                        "module_name": {"type": "string"},
                        "verilog_code": {"type": "string"},
                        "test_scenarios": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["module_name", "verilog_code"]
                }
            )
            
            logger.info(f"✅ 工具注册成功: {list(registry.tools.keys())}")
            
            # 测试工具执行
            tool_call = ToolCall(
                tool_name="generate_testbench",
                parameters={
                    "module_name": "counter",
                    "verilog_code": "module counter(...); endmodule",
                    "test_scenarios": ["test1", "test2"]
                },
                call_id="test_call_001"
            )
            
            result = await registry.execute_tool(tool_call)
            
            if result.success:
                logger.info("✅ 工具执行成功")
                logger.info(f"   结果: {result.result}")
            else:
                logger.error(f"❌ 工具执行失败: {result.error}")
                
        except Exception as e:
            logger.error(f"❌ 工具注册表集成测试失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def run_full_diagnostic(self):
        """运行完整诊断"""
        logger.info("🚀 开始完整诊断...")
        
        try:
            # 1. 测试统一Schema系统
            await self.test_unified_schemas()
            
            # 2. 测试Schema适配器
            await self.test_schema_adapter()
            
            # 3. 测试Schema验证器
            await self.test_schema_validator()
            
            # 4. 测试参数修复器
            await self.test_parameter_repairer()
            
            # 5. 测试字段映射器
            await self.test_field_mapper()
            
            # 6. 测试工具注册表集成
            await self.test_tool_registry_integration()
            
            logger.info("✅ 完整诊断完成")
            
        except Exception as e:
            logger.error(f"❌ 诊断过程失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")

async def main():
    """主函数"""
    diagnostic = ToolExecutionDiagnostic()
    await diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    asyncio.run(main()) 