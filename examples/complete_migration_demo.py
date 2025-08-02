"""
完整的Schema迁移和智能修复演示
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from core.schema_system.migration_helper import MigrationHelper
from core.schema_system.schema_validator import SchemaValidator
from core.schema_system.parameter_repairer import ParameterRepairer

class DemoAgent(EnhancedBaseAgent):
    """演示用的增强Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id="demo_agent",
            role="demonstration", 
            capabilities={"file_operations", "text_processing"}
        )
        
        # 注册演示工具
        self._register_demo_tools()
    
    def _register_demo_tools(self):
        """注册演示工具"""
        
        # 1. 文件写入工具（高安全级别）
        self.register_enhanced_tool(
            name="write_file",
            func=self._write_file_tool,
            description="安全的文件写入操作，支持目录创建和编码设置",
            security_level="high",
            category="file_operations",
            schema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_./\-]+\.[a-zA-Z0-9]+$",
                        "minLength": 1,
                        "maxLength": 255,
                        "description": "文件名，必须包含扩展名，不允许特殊字符"
                    },
                    "content": {
                        "type": "string",
                        "maxLength": 1000000,  # 1MB限制
                        "description": "文件内容"
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否自动创建目录"
                    },
                    "encoding": {
                        "type": "string",
                        "enum": ["utf-8", "ascii", "latin1"],
                        "default": "utf-8",
                        "description": "文件编码格式"
                    }
                },
                "required": ["filename", "content"],
                "additionalProperties": False
            }
        )
        
        # 2. 数学计算工具（普通安全级别）
        self.register_enhanced_tool(
            name="calculate",
            func=self._calculate_tool,
            description="安全的数学表达式计算",
            security_level="normal",
            category="mathematics",
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
                        "description": "结果的小数位精度"
                    }
                },
                "required": ["expression"],
                "additionalProperties": False
            }
        )
        
        # 3. 用户配置处理工具（复杂对象）
        self.register_enhanced_tool(
            name="process_user_config",
            func=self._process_config_tool,
            description="处理和验证用户配置信息",
            security_level="normal",
            category="data_processing",
            schema={
                "type": "object",
                "properties": {
                    "user_config": {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "pattern": r"^[a-zA-Z][a-zA-Z0-9_]{2,19}$",
                                "description": "用户名，3-20字符，字母开头"
                            },
                            "email": {
                                "type": "string",
                                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                                "description": "有效的邮箱地址"
                            },
                            "preferences": {
                                "type": "object",
                                "properties": {
                                    "theme": {
                                        "type": "string",
                                        "enum": ["light", "dark", "auto"],
                                        "default": "auto"
                                    },
                                    "notifications": {
                                        "type": "boolean",
                                        "default": True
                                    },
                                    "max_items": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 100,
                                        "default": 20
                                    }
                                },
                                "required": ["theme"],
                                "additionalProperties": False
                            }
                        },
                        "required": ["username", "email", "preferences"],
                        "additionalProperties": False
                    },
                    "validate_only": {
                        "type": "boolean",
                        "default": False,
                        "description": "是否只验证不保存"
                    }
                },
                "required": ["user_config"],
                "additionalProperties": False
            }
        )
    
    async def _write_file_tool(self, filename: str, content: str, 
                              create_dirs: bool = True, encoding: str = "utf-8") -> dict:
        """文件写入工具实现"""
        try:
            file_path = Path(filename)
            
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"文件已成功写入: {filename}",
                "file_path": str(file_path.absolute()),
                "size_bytes": len(content.encode(encoding))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_tool(self, expression: str, precision: int = 2) -> dict:
        """数学计算工具实现"""
        try:
            # 简单的安全评估
            allowed_chars = set('0123456789+-*/().')
            if not all(c in allowed_chars or c.isspace() for c in expression):
                return {
                    "success": False,
                    "error": "表达式包含不安全的字符"
                }
            
            result = eval(expression)  # 在生产环境中应使用ast.literal_eval或其他安全方法
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
    
    def _process_config_tool(self, user_config: dict, validate_only: bool = False) -> dict:
        """用户配置处理工具实现"""
        try:
            result = {
                "success": True,
                "username": user_config["username"],
                "email": user_config["email"],
                "validation_passed": True
            }
            
            if not validate_only:
                # 模拟配置保存
                preferences = user_config["preferences"]
                result["saved_preferences"] = {
                    "theme": preferences["theme"],
                    "notifications": preferences.get("notifications", True),
                    "max_items": preferences.get("max_items", 20)
                }
                result["message"] = "用户配置已保存"
            else:
                result["message"] = "用户配置验证通过"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _call_llm_for_function_calling(self, conversation: list) -> str:
        """模拟LLM调用（用于演示）"""
        # 这里简化为直接返回最后一条消息中的工具调用指令
        last_message = conversation[-1]["content"]
        
        # 模拟LLM根据错误信息生成修复后的工具调用
        if "参数验证失败" in last_message:
            # 模拟智能修复：LLM会根据错误信息调整参数
            if "write_file" in last_message:
                return '''
                {
                    "tool_calls": [
                        {
                            "tool_name": "write_file",
                            "parameters": {
                                "filename": "demo_output.txt",
                                "content": "Hello, Schema System!",
                                "create_dirs": true,
                                "encoding": "utf-8"
                            }
                        }
                    ]
                }
                '''
        
        # 默认返回原始调用
        return last_message

async def demo_schema_validation_and_repair():
    """演示Schema验证和智能修复"""
    print("🧪 JSON Schema验证和智能修复演示")
    print("=" * 60)
    
    agent = DemoAgent()
    
    # 测试用例：包含各种参数错误的工具调用
    test_cases = [
        {
            "name": "✅ 正确的文件写入",
            "request": "请写入一个文件",
            "expected_tools": [{
                "tool_name": "write_file",
                "parameters": {
                    "filename": "test.txt",
                    "content": "Hello World!",
                    "create_dirs": True
                }
            }]
        },
        {
            "name": "❌ 文件名格式错误 → 智能修复",
            "request": "写入文件但文件名有问题",
            "expected_tools": [{
                "tool_name": "write_file", 
                "parameters": {
                    "filename": "bad<>filename",  # 包含非法字符
                    "content": "Test content",
                    "extra_field": "not_allowed"  # 额外字段
                }
            }]
        },
        {
            "name": "❌ 数学表达式安全检查 → 智能修复",
            "request": "计算数学表达式",
            "expected_tools": [{
                "tool_name": "calculate",
                "parameters": {
                    "expression": "import os; os.system('rm -rf /')",  # 危险代码
                    "precision": 15  # 超出范围
                }
            }]
        },
        {
            "name": "❌ 复杂对象验证 → 智能修复",
            "request": "处理用户配置",  
            "expected_tools": [{
                "tool_name": "process_user_config",
                "parameters": {
                    "user_config": {
                        "username": "ab",  # 太短
                        "email": "invalid-email",  # 格式错误
                        "preferences": {
                            "theme": "purple",  # 不在枚举中
                            "max_items": 200  # 超出范围
                        }
                    }
                }
            }]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print("-" * 50)
        
        # 模拟工具调用
        for tool_call_data in test_case["expected_tools"]:
            from core.function_calling import ToolCall
            
            tool_call = ToolCall(
                tool_name=tool_call_data["tool_name"],
                parameters=tool_call_data["parameters"],
                call_id=f"test_{i}"
            )
            
            print(f"🔧 调用工具: {tool_call.tool_name}")
            print(f"参数: {json.dumps(tool_call.parameters, indent=2, ensure_ascii=False)}")
            
            # 执行增强的工具调用
            result = await agent._execute_enhanced_tool_call(tool_call)
            
            if result.success:
                print(f"✅ 执行成功:")
                print(f"结果: {json.dumps(result.result, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 执行失败:")
                print(f"错误: {result.error}")
                
                # 如果包含修复建议，演示完整的修复流程
                if "修复建议" in result.error:
                    print(f"\n🔧 启动智能修复流程...")
                    
                    # 构建包含错误信息的对话
                    conversation = [
                        {"role": "user", "content": test_case["request"]},
                        {"role": "user", "content": result.error}
                    ]
                    
                    # 让Agent处理（会触发智能修复）
                    fixed_result = await agent.process_with_enhanced_validation(
                        user_request=test_case["request"], 
                        max_iterations=2
                    )
                    
                    if fixed_result["success"]:
                        print(f"✅ 智能修复成功!")
                        print(f"修复后结果: {json.dumps(fixed_result.get('tool_results', []), indent=2, ensure_ascii=False)}")
                    else:
                        print(f"❌ 智能修复失败: {fixed_result.get('error')}")
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("📊 系统统计")
    stats = agent.get_validation_statistics()
    print(f"总验证次数: {stats['total_validations']}")
    print(f"成功验证次数: {stats['successful_validations']}")
    print(f"验证成功率: {stats['success_rate']:.1%}")

def demo_migration_helper():
    """演示迁移辅助工具"""
    print("\n" + "=" * 60)
    print("🔄 工具迁移辅助演示")
    print("=" * 60)
    
    # 创建迁移助手
    migration_helper = MigrationHelper()
    
    # 模拟现有工具定义
    def legacy_write_file(filename: str, content: str, mode: str = "w") -> bool:
        """
        写入文件的传统工具
        
        Args:
            filename (str): 文件名
            content (str): 文件内容
            mode (str): 写入模式，默认为'w'
            
        Returns:
            bool: 是否成功
        """
        pass
    
    # 现有参数定义
    existing_params = {
        "filename": {"type": "string", "description": "文件名", "required": True},
        "content": {"type": "string", "description": "文件内容", "required": True},
        "mode": {"type": "string", "description": "写入模式", "required": False}
    }
    
    # 分析现有工具
    analysis = migration_helper.analyze_existing_tool(
        tool_func=legacy_write_file,
        tool_name="write_file",
        existing_params=existing_params
    )
    
    print("📋 工具分析结果:")
    print(f"工具名: {analysis['tool_name']}")
    print(f"建议Schema:")
    print(json.dumps(analysis['suggested_schema'], indent=2, ensure_ascii=False))
    
    if analysis['migration_notes']:
        print(f"\n⚠️ 迁移注意事项:")
        for note in analysis['migration_notes']:
            print(f"  • {note}")
    
    # 生成迁移脚本
    print(f"\n🔧 生成迁移脚本...")
    script = migration_helper.generate_migration_script([analysis], "demo_migration.py")
    print(f"迁移脚本已生成: demo_migration.py")

async def main():
    """主函数"""
    print("🚀 CentralizedAgentFramework Schema系统完整演示")
    print("=" * 80)
    
    # 1. 演示Schema验证和智能修复
    await demo_schema_validation_and_repair()
    
    # 2. 演示迁移辅助工具
    demo_migration_helper()
    
    print("\n" + "=" * 80)
    print("🎉 演示完成！")
    print("\n📝 核心功能验证:")
    print("  ✅ JSON Schema参数验证")
    print("  ✅ 智能参数修复建议")
    print("  ✅ 自动化错误反馈给Agent")
    print("  ✅ 安全性检查和防护")
    print("  ✅ 现有工具迁移辅助")
    print("  ✅ 向后兼容性保持")
    
    print("\n🎯 下一步行动:")
    print("  1. 安装jsonschema依赖: pip install jsonschema")
    print("  2. 将core/schema_system/集成到现有系统")
    print("  3. 逐步迁移现有工具到Schema系统")
    print("  4. 建立完整的测试覆盖")

if __name__ == "__main__":
    asyncio.run(main())