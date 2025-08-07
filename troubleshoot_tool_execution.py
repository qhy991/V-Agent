#!/usr/bin/env python3
"""
工具执行问题排查脚本
专门用于排查工具执行引擎的路由逻辑问题
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
from core.enhanced_tool_registry import EnhancedToolRegistry

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ToolExecutionTroubleshooter:
    """工具执行问题排查器"""
    
    def __init__(self):
        self.schema_adapter = FlexibleSchemaAdapter()
        self.schema_validator = SchemaValidator()
        self.parameter_repairer = ParameterRepairer()
        self.tool_registry = EnhancedToolRegistry()
        
    async def setup_test_environment(self):
        """设置测试环境"""
        logger.info("🔧 设置测试环境...")
        
        # 注册真实的 generate_testbench 工具
        await self._register_real_tools()
        
        logger.info("✅ 测试环境设置完成")
    
    async def _register_real_tools(self):
        """注册真实的工具"""
        logger.info("📝 注册真实工具...")
        
        # 模拟真实的 generate_testbench 工具
        def real_generate_testbench(module_name: str, verilog_code: str, test_scenarios: list = None):
            return {
                "success": True,
                "testbench_code": f"// Testbench for {module_name}\nmodule {module_name}_tb;\n// ...",
                "message": "Testbench generated successfully"
            }
        
        # 注册工具
        self.tool_registry.register_tool(
            name="generate_testbench",
            func=real_generate_testbench,
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
        
        logger.info(f"✅ 已注册工具: {list(self.tool_registry.tools.keys())}")
    
    async def test_tool_execution_flow(self):
        """测试完整的工具执行流程"""
        logger.info("🔍 测试完整的工具执行流程...")
        
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
        
        logger.info(f"📋 工具调用: {tool_call.tool_name}")
        logger.info(f"📋 参数: {tool_call.parameters}")
        
        # 步骤1: 检查工具是否注册
        if tool_call.tool_name not in self.tool_registry.tools:
            logger.error(f"❌ 工具 {tool_call.tool_name} 未在注册表中")
            return
        
        logger.info("✅ 工具在注册表中")
        
        # 步骤2: 获取工具定义
        tool_func = self.tool_registry.tools[tool_call.tool_name]
        logger.info(f"✅ 获取工具函数: {tool_func}")
        
        # 步骤3: 验证参数
        is_valid, error_msg = self.tool_registry.validate_parameters(
            tool_call.tool_name, tool_call.parameters
        )
        
        if not is_valid:
            logger.error(f"❌ 参数验证失败: {error_msg}")
            return
        
        logger.info("✅ 参数验证通过")
        
        # 步骤4: 执行工具
        try:
            result = await self.tool_registry.execute_tool(tool_call)
            
            if result.success:
                logger.info("✅ 工具执行成功")
                logger.info(f"   结果: {result.result}")
            else:
                logger.error(f"❌ 工具执行失败: {result.error}")
                
        except Exception as e:
            logger.error(f"❌ 工具执行异常: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
    
    async def test_enhanced_validation_flow(self):
        """测试增强验证流程"""
        logger.info("🔍 测试增强验证流程...")
        
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
        
        # 步骤1: 统一Schema标准化
        try:
            normalized_params = UnifiedSchemas.validate_and_normalize_parameters(
                tool_call.tool_name, tool_call.parameters
            )
            logger.info(f"✅ 统一Schema标准化: {normalized_params}")
        except Exception as e:
            logger.error(f"❌ 统一Schema标准化失败: {e}")
            return
        
        # 步骤2: Schema适配
        try:
            schema = {
                "type": "object",
                "properties": {
                    "module_name": {"type": "string"},
                    "verilog_code": {"type": "string"},
                    "test_scenarios": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["module_name", "verilog_code"]
            }
            
            adaptation_result = self.schema_adapter.adapt_parameters(
                normalized_params, schema, tool_call.tool_name
            )
            
            if adaptation_result.success:
                logger.info(f"✅ Schema适配成功: {adaptation_result.adapted_data}")
            else:
                logger.error(f"❌ Schema适配失败: {adaptation_result.warnings}")
                return
                
        except Exception as e:
            logger.error(f"❌ Schema适配异常: {e}")
            return
        
        # 步骤3: Schema验证
        try:
            validation_result = self.schema_validator.validate(
                adaptation_result.adapted_data, schema
            )
            
            if validation_result.is_valid:
                logger.info("✅ Schema验证通过")
            else:
                logger.error(f"❌ Schema验证失败: {validation_result.get_error_summary()}")
                
                # 尝试参数修复
                repair_result = self.parameter_repairer.repair_parameters(
                    adaptation_result.adapted_data, schema, validation_result
                )
                
                if repair_result.success:
                    logger.info(f"✅ 参数修复成功: {repair_result.repaired_data}")
                else:
                    logger.error(f"❌ 参数修复失败")
                    return
                    
        except Exception as e:
            logger.error(f"❌ Schema验证异常: {e}")
            return
        
        logger.info("✅ 增强验证流程完成")
    
    async def test_error_scenarios(self):
        """测试错误场景"""
        logger.info("🔍 测试错误场景...")
        
        # 场景1: 工具不存在
        logger.info("📋 场景1: 工具不存在")
        non_existent_tool_call = ToolCall(
            tool_name="non_existent_tool",
            parameters={},
            call_id="test_call_003"
        )
        
        try:
            result = await self.tool_registry.execute_tool(non_existent_tool_call)
            logger.info(f"结果: {result.success}, 错误: {result.error}")
        except Exception as e:
            logger.error(f"异常: {e}")
        
        # 场景2: 参数验证失败
        logger.info("📋 场景2: 参数验证失败")
        invalid_params_tool_call = ToolCall(
            tool_name="generate_testbench",
            parameters={
                "module_name": 123,  # 应该是字符串
                "verilog_code": None  # 应该是字符串
            },
            call_id="test_call_004"
        )
        
        try:
            result = await self.tool_registry.execute_tool(invalid_params_tool_call)
            logger.info(f"结果: {result.success}, 错误: {result.error}")
        except Exception as e:
            logger.error(f"异常: {e}")
        
        # 场景3: 工具执行异常
        logger.info("📋 场景3: 工具执行异常")
        
        # 注册一个会抛出异常的工具
        def failing_tool():
            raise Exception("模拟工具执行失败")
        
        self.tool_registry.register_tool(
            name="failing_tool",
            func=failing_tool,
            description="A tool that always fails",
            schema={"type": "object"}
        )
        
        failing_tool_call = ToolCall(
            tool_name="failing_tool",
            parameters={},
            call_id="test_call_005"
        )
        
        try:
            result = await self.tool_registry.execute_tool(failing_tool_call)
            logger.info(f"结果: {result.success}, 错误: {result.error}")
        except Exception as e:
            logger.error(f"异常: {e}")
    
    async def test_performance_and_timeout(self):
        """测试性能和超时"""
        logger.info("🔍 测试性能和超时...")
        
        # 注册一个慢速工具
        async def slow_tool():
            await asyncio.sleep(2)  # 模拟慢速执行
            return {"success": True, "message": "Slow tool completed"}
        
        self.tool_registry.register_tool(
            name="slow_tool",
            func=slow_tool,
            description="A slow tool for testing",
            schema={"type": "object"}
        )
        
        slow_tool_call = ToolCall(
            tool_name="slow_tool",
            parameters={},
            call_id="test_call_006"
        )
        
        try:
            start_time = asyncio.get_event_loop().time()
            result = await self.tool_registry.execute_tool(slow_tool_call)
            end_time = asyncio.get_event_loop().time()
            
            logger.info(f"执行时间: {end_time - start_time:.2f}秒")
            logger.info(f"结果: {result.success}, 错误: {result.error}")
            
        except Exception as e:
            logger.error(f"异常: {e}")
    
    async def run_comprehensive_troubleshooting(self):
        """运行全面的问题排查"""
        logger.info("🚀 开始全面的问题排查...")
        
        try:
            # 1. 设置测试环境
            await self.setup_test_environment()
            
            # 2. 测试完整的工具执行流程
            await self.test_tool_execution_flow()
            
            # 3. 测试增强验证流程
            await self.test_enhanced_validation_flow()
            
            # 4. 测试错误场景
            await self.test_error_scenarios()
            
            # 5. 测试性能和超时
            await self.test_performance_and_timeout()
            
            logger.info("✅ 全面的问题排查完成")
            
        except Exception as e:
            logger.error(f"❌ 问题排查过程失败: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")

async def main():
    """主函数"""
    troubleshooter = ToolExecutionTroubleshooter()
    await troubleshooter.run_comprehensive_troubleshooting()

if __name__ == "__main__":
    asyncio.run(main()) 