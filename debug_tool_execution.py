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

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
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
        self.enhanced_agent = None
        self.schema_adapter = FlexibleSchemaAdapter()
        self.schema_validator = SchemaValidator()
        self.parameter_repairer = ParameterRepairer()
        
    async def setup_test_environment(self):
        """设置测试环境"""
        logger.info("🔧 设置测试环境...")
        
        # 创建增强智能体
        self.enhanced_agent = EnhancedBaseAgent(
            agent_id="diagnostic_agent",
            role="diagnostic",
            capabilities={"diagnostic", "testing"}
        )
        
        # 注册测试工具
        await self._register_test_tools()
        
        logger.info("✅ 测试环境设置完成")
    
    async def _register_test_tools(self):
        """注册测试工具"""
        logger.info("📝 注册测试工具...")
        
        # 模拟 generate_testbench 工具
        def mock_generate_testbench(module_name: str, verilog_code: str, test_scenarios: list = None):
            return {
                "success": True,
                "testbench_code": f"// Testbench for {module_name}\nmodule {module_name}_tb;\n// ...",
                "message": "Testbench generated successfully"
            }
        
        # 注册工具
        self.enhanced_agent.register_enhanced_tool(
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
        
        logger.info(f"✅ 已注册工具: {list(self.enhanced_agent.enhanced_tools.keys())}")
    
    async def test_tool_registration(self):
        """测试工具注册"""
        logger.info("🔍 测试工具注册...")
        
        # 检查工具是否在增强注册表中
        if "generate_testbench" in self.enhanced_agent.enhanced_tools:
            logger.info("✅ generate_testbench 在增强注册表中")
            tool_def = self.enhanced_agent.enhanced_tools["generate_testbench"]
            logger.info(f"   工具定义: {tool_def.name}, 描述: {tool_def.description}")
        else:
            logger.error("❌ generate_testbench 不在增强注册表中")
        
        # 检查传统注册表
        if hasattr(self.enhanced_agent, '_function_registry_backup'):
            if "generate_testbench" in self.enhanced_agent._function_registry_backup:
                logger.info("✅ generate_testbench 在传统注册表中")
            else:
                logger.warning("⚠️ generate_testbench 不在传统注册表中")
    
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
    
    async def test_enhanced_tool_execution(self):
        """测试增强工具执行"""
        logger.info("🔍 测试增强工具执行...")
        
        try:
            # 创建工具调用
            tool_call = ToolCall(
                tool_name="generate_testbench",
                parameters={
                    "module_name": "counter",
                    "verilog_code": "module counter(...); endmodule",
                    "test_scenarios": ["test1", "test2"]
                },
                call_id="test_call_001"
            )
            
            # 执行工具调用
            result = await self.enhanced_agent._execute_enhanced_tool_call(tool_call)
            
            if result.success:
                logger.info("✅ 增强工具执行成功")
                logger.info(f"   结果: {result.result}")
            else:
                logger.error(f"❌ 增强工具执行失败: {result.error}")
                
        except Exception as e:
            logger.error(f"❌ 增强工具执行测试失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def test_traditional_tool_execution(self):
        """测试传统工具执行"""
        logger.info("🔍 测试传统工具执行...")
        
        try:
            # 创建工具调用
            tool_call = ToolCall(
                tool_name="generate_testbench",
                parameters={
                    "module_name": "counter",
                    "verilog_code": "module counter(...); endmodule",
                    "test_scenarios": ["test1", "test2"]
                },
                call_id="test_call_002"
            )
            
            # 执行工具调用
            result = await self.enhanced_agent._execute_tool_call_with_retry(tool_call)
            
            if result.success:
                logger.info("✅ 传统工具执行成功")
                logger.info(f"   结果: {result.result}")
            else:
                logger.error(f"❌ 传统工具执行失败: {result.error}")
                
        except Exception as e:
            logger.error(f"❌ 传统工具执行测试失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def run_full_diagnostic(self):
        """运行完整诊断"""
        logger.info("🚀 开始完整诊断...")
        
        try:
            # 1. 设置测试环境
            await self.setup_test_environment()
            
            # 2. 测试工具注册
            await self.test_tool_registration()
            
            # 3. 测试统一Schema系统
            await self.test_unified_schemas()
            
            # 4. 测试Schema适配器
            await self.test_schema_adapter()
            
            # 5. 测试Schema验证器
            await self.test_schema_validator()
            
            # 6. 测试增强工具执行
            await self.test_enhanced_tool_execution()
            
            # 7. 测试传统工具执行
            await self.test_traditional_tool_execution()
            
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