#!/usr/bin/env python3
"""
Schema系统集成测试 - 验证完整的智能修复流程
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.function_calling import ToolCall
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestSchemaAgent(EnhancedBaseAgent):
    """测试用的Schema增强Agent"""
    
    def __init__(self):
        from core.enums import AgentCapability
        super().__init__(
            agent_id="test_schema_agent",
            role="testing",
            capabilities={AgentCapability.CODE_GENERATION, AgentCapability.TEST_GENERATION}
        )
        
        # 注册测试工具
        self._register_test_tools()
    
    def get_capabilities(self) -> set:
        """获取智能体能力"""
        from core.enums import AgentCapability
        return {AgentCapability.CODE_GENERATION, AgentCapability.TEST_GENERATION}
    
    def get_specialty_description(self) -> str:
        """获取专业描述"""
        return "Schema系统测试专用智能体，用于验证参数验证和智能修复功能"
    
    async def execute_enhanced_task(self, enhanced_prompt: str, original_message, quality_requirements: dict = None) -> dict:
        """执行增强任务"""
        return {
            "success": True,
            "message": "测试任务执行完成",
            "result": "Enhanced task execution for testing"
        }
    
    def _register_test_tools(self):
        """注册测试工具"""
        
        # 1. 文件写入工具 - 高安全级别
        self.register_enhanced_tool(
            name="write_file",
            func=self._tool_write_file,
            description="安全的文件写入操作",
            security_level="high",
            schema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_./\-]+\.[a-zA-Z0-9]+$",
                        "maxLength": 255,
                        "description": "文件名，必须包含扩展名"
                    },
                    "content": {
                        "type": "string",
                        "maxLength": 100000,
                        "description": "文件内容"
                    },
                    "encoding": {
                        "type": "string",
                        "enum": ["utf-8", "ascii", "latin1"],
                        "default": "utf-8",
                        "description": "文件编码"
                    }
                },
                "required": ["filename", "content"],
                "additionalProperties": False
            }
        )
        
        # 2. Verilog代码生成工具
        self.register_enhanced_tool(
            name="generate_verilog_code",
            func=self._tool_generate_verilog,
            description="生成Verilog HDL代码",
            security_level="normal",
            schema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                        "maxLength": 100,
                        "description": "模块名称，必须以字母开头"
                    },
                    "input_ports": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 50,
                        "description": "输入端口列表"
                    },
                    "output_ports": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "maxItems": 50,
                        "description": "输出端口列表"
                    },
                    "functionality": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 10000,
                        "description": "功能描述"
                    }
                },
                "required": ["module_name", "functionality"],
                "additionalProperties": False
            }
        )
        
        # 3. 数学计算工具
        self.register_enhanced_tool(
            name="calculate",
            func=self._tool_calculate,
            description="安全的数学表达式计算",
            security_level="normal",
            schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "pattern": r"^[0-9+\-*/().\s]+$",
                        "maxLength": 1000,
                        "description": "数学表达式，只允许数字和基本运算符"
                    },
                    "precision": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 10,
                        "default": 2,
                        "description": "结果精度"
                    }
                },
                "required": ["expression"],
                "additionalProperties": False
            }
        )
    
    async def _tool_write_file(self, filename: str, content: str, encoding: str = "utf-8") -> dict:
        """文件写入工具实现"""
        try:
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"文件写入成功: {filename}",
                "size": len(content),
                "encoding": encoding
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_generate_verilog(self, module_name: str, functionality: str, 
                                   input_ports: list = None, output_ports: list = None) -> dict:
        """Verilog代码生成工具实现"""
        try:
            # 简单的Verilog代码生成
            verilog_code = f"module {module_name}(\n"
            
            if input_ports:
                for port in input_ports:
                    verilog_code += f"    input {port},\n"
            
            if output_ports:
                for port in output_ports:
                    verilog_code += f"    output {port},\n"
            
            verilog_code = verilog_code.rstrip(',\n') + "\n);\n\n"
            verilog_code += f"    // {functionality}\n\n"
            verilog_code += "endmodule\n"
            
            return {
                "success": True,
                "verilog_code": verilog_code,
                "module_name": module_name,
                "lines": len(verilog_code.split('\n'))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _tool_calculate(self, expression: str, precision: int = 2) -> dict:
        """数学计算工具实现"""
        try:
            # 安全检查
            allowed_chars = set('0123456789+-*/().')
            if not all(c in allowed_chars or c.isspace() for c in expression):
                return {
                    "success": False,
                    "error": "表达式包含不安全字符"
                }
            
            result = eval(expression)
            rounded_result = round(float(result), precision)
            
            return {
                "success": True,
                "expression": expression,
                "result": rounded_result,
                "precision": precision
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"计算错误: {str(e)}"
            }
    
    async def _call_llm_for_function_calling(self, conversation: list) -> str:
        """模拟LLM调用 - 根据错误信息智能修复参数"""
        last_message = conversation[-1]["content"]
        
        # 如果收到参数验证失败的错误，模拟智能修复
        if "参数验证失败" in last_message:
            logger.info("🤖 LLM检测到参数验证失败，正在生成修复后的调用...")
            
            # 根据错误类型返回修复后的调用
            if "write_file" in last_message:
                if "文件名" in last_message or "pattern" in last_message:
                    return json.dumps({
                        "tool_calls": [{
                            "tool_name": "write_file",
                            "parameters": {
                                "filename": "test_output.txt",  # 修复文件名
                                "content": "Hello, Schema System!",
                                "encoding": "utf-8"
                            }
                        }]
                    })
            
            elif "generate_verilog_code" in last_message:
                if "module_name" in last_message:
                    return json.dumps({
                        "tool_calls": [{
                            "tool_name": "generate_verilog_code", 
                            "parameters": {
                                "module_name": "counter_module",  # 修复模块名
                                "functionality": "A simple 8-bit counter that increments on each clock cycle",
                                "input_ports": ["clk", "rst"],
                                "output_ports": ["count"]
                            }
                        }]
                    })
            
            elif "calculate" in last_message:
                if "expression" in last_message:
                    return json.dumps({
                        "tool_calls": [{
                            "tool_name": "calculate",
                            "parameters": {
                                "expression": "2 + 3 * 4",  # 修复表达式
                                "precision": 2
                            }
                        }]
                    })
        
        # 默认返回空响应
        return "我需要更多信息来完成任务。"

async def test_schema_validation_and_repair():
    """测试Schema验证和智能修复功能"""
    print("🧪 测试Schema验证和智能修复功能")
    print("=" * 60)
    
    agent = TestSchemaAgent()
    
    # 测试用例：包含各种参数错误
    test_cases = [
        {
            "name": "✅ 正常的文件写入",
            "tool_call": ToolCall(
                tool_name="write_file",
                parameters={
                    "filename": "test.txt",
                    "content": "Hello World!",
                    "encoding": "utf-8"
                },
                call_id="test1"
            ),
            "expected_success": True
        },
        {
            "name": "❌ 文件名包含非法字符 → 智能修复",
            "tool_call": ToolCall(
                tool_name="write_file",
                parameters={
                    "filename": "bad<>filename",  # 非法字符
                    "content": "Test content",
                    "extra_field": "not_allowed"  # 额外字段
                },
                call_id="test2"
            ),
            "expected_success": False,
            "should_repair": True
        },
        {
            "name": "❌ 模块名格式错误 → 智能修复",
            "tool_call": ToolCall(
                tool_name="generate_verilog_code",
                parameters={
                    "module_name": "123invalid",  # 数字开头
                    "functionality": "test",  # 太短
                    "input_ports": ["clk"]
                },
                call_id="test3"
            ),
            "expected_success": False,
            "should_repair": True
        },
        {
            "name": "❌ 数学表达式包含危险代码 → 智能修复", 
            "tool_call": ToolCall(
                tool_name="calculate",
                parameters={
                    "expression": "import os; os.system('rm -rf /')",  # 危险代码
                    "precision": 15  # 超出范围
                },
                call_id="test4"
            ),
            "expected_success": False,
            "should_repair": True
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print("-" * 50)
        
        # 执行工具调用
        result = await agent._execute_enhanced_tool_call(test_case["tool_call"])
        
        print(f"🔧 工具: {test_case['tool_call'].tool_name}")
        print(f"参数: {json.dumps(test_case['tool_call'].parameters, indent=2, ensure_ascii=False)}")
        
        if result.success:
            print("✅ 执行成功")
            print(f"结果: {json.dumps(result.result, indent=2, ensure_ascii=False)}")
            results.append({"test": i, "success": True, "repaired": False})
        else:
            print("❌ 执行失败") 
            print(f"错误: {result.error}")
            
            # 如果应该能修复，测试完整的修复流程
            if test_case.get("should_repair"):
                print("\n🔧 启动智能修复流程...")
                
                # 构建模拟用户请求
                user_request = f"请使用{test_case['tool_call'].tool_name}工具"
                
                # 使用完整的智能修复流程
                repair_result = await agent.process_with_enhanced_validation(
                    user_request=user_request,
                    max_iterations=3
                )
                
                if repair_result["success"]:
                    print("✅ 智能修复成功!")
                    print(f"修复后结果: {json.dumps(repair_result.get('tool_results', []), indent=2, ensure_ascii=False)}")
                    results.append({"test": i, "success": True, "repaired": True})
                else:
                    print(f"❌ 智能修复失败: {repair_result.get('error')}")
                    results.append({"test": i, "success": False, "repaired": False})
            else:
                results.append({"test": i, "success": False, "repaired": False})
    
    # 统计结果
    print("\n" + "=" * 60)
    print("📊 测试结果统计")
    print("-" * 30)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    repaired_tests = sum(1 for r in results if r["repaired"])
    
    print(f"总测试数: {total_tests}")
    print(f"成功测试数: {successful_tests}")
    print(f"智能修复成功: {repaired_tests}")
    print(f"成功率: {successful_tests/total_tests:.1%}")
    print(f"修复率: {repaired_tests/(total_tests-1):.1%}")  # 排除第一个正常测试
    
    # 显示验证统计
    stats = agent.get_validation_statistics()
    print(f"\n📈 验证统计:")
    print(f"总验证次数: {stats['total_validations']}")
    print(f"成功验证次数: {stats['successful_validations']}")
    print(f"验证成功率: {stats['success_rate']:.1%}")
    
    return results

async def test_real_agent_integration():
    """测试与现有Agent的集成"""
    print("\n" + "=" * 60)
    print("🔄 测试与现有Agent的集成")
    print("=" * 60)
    
    try:
        # 尝试导入现有的Agent
        from agents.real_verilog_agent import RealVerilogDesignAgent
        
        # 创建现有Agent的增强版本
        agent = RealVerilogDesignAgent()
        
        # 检查是否有增强功能
        if hasattr(agent, 'enhanced_tools'):
            print("✅ Agent已集成Schema系统")
            enhanced_tools = agent.list_enhanced_tools()
            print(f"增强工具数量: {len(enhanced_tools)}")
            for tool in enhanced_tools:
                print(f"  - {tool['name']} ({tool['security_level']})")
        else:
            print("⚠️ Agent尚未集成Schema系统")
            print("建议按照迁移计划进行升级")
        
    except ImportError as e:
        print(f"⚠️ 无法导入现有Agent: {str(e)}")
        print("这是正常的，说明还没有完成迁移")

async def main():
    """主测试函数"""
    print("🚀 CentralizedAgentFramework Schema系统集成测试")
    print("=" * 80)
    
    try:
        # 1. 测试Schema验证和智能修复
        results = await test_schema_validation_and_repair()
        
        # 2. 测试与现有系统的集成
        await test_real_agent_integration()
        
        print("\n" + "=" * 80)
        print("🎉 Schema系统集成测试完成!")
        
        # 分析测试结果
        successful_tests = sum(1 for r in results if r["success"])
        repair_tests = sum(1 for r in results if r["repaired"])
        
        if successful_tests == len(results):
            print("✅ 所有测试通过 - Schema系统运行正常")
        else:
            print(f"⚠️ {len(results) - successful_tests} 个测试失败")
        
        if repair_tests > 0:
            print(f"🔧 智能修复功能正常，成功修复 {repair_tests} 个参数错误")
        
        print("\n📝 下一步建议:")
        print("1. 完成现有Agent的Schema系统集成")
        print("2. 建立完整的测试覆盖")
        print("3. 逐步在生产环境中启用Schema验证")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        logger.exception("测试异常")
        
        print("\n🔧 故障排除建议:")
        print("1. 检查依赖是否正确安装: pip install jsonschema")
        print("2. 确保core/schema_system模块正确实现")
        print("3. 检查日志文件获取详细错误信息")

if __name__ == "__main__":
    asyncio.run(main())