"""
增强工具系统使用示例 - JSON Schema验证
"""
import asyncio
import json
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.enhanced_tool_registry import EnhancedToolRegistry
from core.function_calling import ToolCall

class ExampleToolAgent:
    """示例智能体 - 使用增强工具系统"""
    
    def __init__(self):
        self.tool_registry = EnhancedToolRegistry()
        self._register_tools()
    
    def _register_tools(self):
        """注册示例工具"""
        
        # 1. 文件操作工具（高安全级别）
        self.tool_registry.register_tool(
            name="write_file",
            func=self._write_file,
            description="将内容写入文件，支持创建目录",
            category="file_operations",
            security_level="high",
            schema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "pattern": "^[a-zA-Z0-9_./\\-]+\\.[a-zA-Z0-9]+$",
                        "minLength": 1,
                        "maxLength": 255,
                        "description": "文件名，必须包含扩展名，支持相对路径"
                    },
                    "content": {
                        "type": "string",
                        "maxLength": 1000000,
                        "description": "文件内容，最大1MB"
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
                        "description": "文件编码"
                    }
                },
                "required": ["filename", "content"],
                "additionalProperties": False
            }
        )
        
        # 2. 数学计算工具（普通安全级别）
        self.tool_registry.register_tool(
            name="calculate",
            func=self._calculate,
            description="执行数学运算",
            category="mathematics",
            security_level="normal",
            schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "pattern": "^[0-9+\\-*/()\\s.]+$",
                        "maxLength": 1000,
                        "description": "数学表达式，只允许数字和基本运算符"
                    },
                    "precision": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 10,
                        "default": 2,
                        "description": "小数位精度"
                    }
                },
                "required": ["expression"],
                "additionalProperties": False
            }
        )
        
        # 3. 文本处理工具（低安全级别）
        self.tool_registry.register_tool(
            name="process_text",
            func=self._process_text,
            description="处理文本内容",
            category="text_processing",
            security_level="low",
            schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "maxLength": 10000,
                        "description": "要处理的文本"
                    },
                    "operations": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["uppercase", "lowercase", "title", "strip", "reverse"]
                        },
                        "minItems": 1,
                        "maxItems": 5,
                        "description": "要执行的操作列表"
                    },
                    "word_count": {
                        "type": "boolean",
                        "default": False,
                        "description": "是否返回字数统计"
                    }
                },
                "required": ["text", "operations"],
                "additionalProperties": False
            }
        )
        
        # 4. 复杂对象处理工具
        self.tool_registry.register_tool(
            name="process_config",
            func=self._process_config,
            description="处理配置文件数据",
            category="data_processing",
            security_level="normal",
            schema={
                "type": "object",
                "properties": {
                    "config": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                            "settings": {
                                "type": "object",
                                "properties": {
                                    "debug": {"type": "boolean"},
                                    "max_workers": {"type": "integer", "minimum": 1, "maximum": 100},
                                    "features": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["debug"],
                                "additionalProperties": False
                            }
                        },
                        "required": ["name", "version", "settings"],
                        "additionalProperties": False
                    },
                    "validate_only": {
                        "type": "boolean",
                        "default": False,
                        "description": "是否只验证不处理"
                    }
                },
                "required": ["config"],
                "additionalProperties": False
            }
        )
    
    async def _write_file(self, filename: str, content: str, 
                         create_dirs: bool = True, encoding: str = "utf-8") -> dict:
        """写文件工具实现"""
        try:
            file_path = Path(filename)
            
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"文件已写入: {filename}",
                "size_bytes": len(content.encode(encoding)),
                "path": str(file_path.absolute())
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate(self, expression: str, precision: int = 2) -> dict:
        """数学计算工具实现"""
        try:
            # 简单的安全评估 - 只允许基本数学运算
            allowed_chars = set('0123456789+-*/().')
            if not all(c in allowed_chars or c.isspace() for c in expression):
                return {
                    "success": False,
                    "error": "表达式包含不允许的字符"
                }
            
            result = eval(expression)  # 在生产环境中应使用更安全的方法
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
    
    def _process_text(self, text: str, operations: list, word_count: bool = False) -> dict:
        """文本处理工具实现"""
        try:
            result_text = text
            applied_operations = []
            
            for operation in operations:
                if operation == "uppercase":
                    result_text = result_text.upper()
                elif operation == "lowercase":
                    result_text = result_text.lower()
                elif operation == "title":
                    result_text = result_text.title()
                elif operation == "strip":
                    result_text = result_text.strip()
                elif operation == "reverse":
                    result_text = result_text[::-1]
                
                applied_operations.append(operation)
            
            result = {
                "success": True,
                "original_text": text,
                "processed_text": result_text,
                "applied_operations": applied_operations
            }
            
            if word_count:
                result["word_count"] = len(result_text.split())
                result["character_count"] = len(result_text)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_config(self, config: dict, validate_only: bool = False) -> dict:
        """配置处理工具实现"""
        try:
            result = {
                "success": True,
                "config_name": config["name"],
                "config_version": config["version"],
                "validation": "passed"
            }
            
            if not validate_only:
                # 模拟配置处理
                settings = config["settings"]
                result["processed_settings"] = {
                    "debug_mode": settings["debug"],
                    "worker_count": settings.get("max_workers", 4),
                    "enabled_features": settings.get("features", [])
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_tools(self):
        """测试工具调用"""
        print("🧪 测试增强工具系统")
        print("=" * 50)
        
        # 测试用例
        test_cases = [
            # 1. 成功的文件写入
            ToolCall(
                tool_name="write_file",
                parameters={
                    "filename": "test_output/example.txt",
                    "content": "Hello, Enhanced Tool System!",
                    "create_dirs": True
                },
                call_id="test_1"
            ),
            
            # 2. 数学计算
            ToolCall(
                tool_name="calculate",
                parameters={
                    "expression": "2 + 3 * 4 / 2",
                    "precision": 3
                },
                call_id="test_2"
            ),
            
            # 3. 文本处理
            ToolCall(
                tool_name="process_text",
                parameters={
                    "text": "  hello world  ",
                    "operations": ["strip", "title", "reverse"],
                    "word_count": True
                },
                call_id="test_3"
            ),
            
            # 4. 复杂配置处理
            ToolCall(
                tool_name="process_config",
                parameters={
                    "config": {
                        "name": "MyApp",
                        "version": "1.2.3",
                        "settings": {
                            "debug": True,
                            "max_workers": 8,
                            "features": ["feature1", "feature2"]
                        }
                    },
                    "validate_only": False
                },
                call_id="test_4"
            ),
            
            # 5. 参数验证失败的案例
            ToolCall(
                tool_name="write_file",
                parameters={
                    "filename": "../../../etc/passwd",  # 危险路径
                    "content": "malicious content"
                },
                call_id="test_5"
            ),
            
            # 6. 不正确的数学表达式
            ToolCall(
                tool_name="calculate",
                parameters={
                    "expression": "import os; os.system('ls')",  # 危险代码
                    "precision": 2
                },
                call_id="test_6"
            )
        ]
        
        # 执行测试
        for i, tool_call in enumerate(test_cases, 1):
            print(f"\n📋 测试 {i}: {tool_call.tool_name}")
            print(f"参数: {json.dumps(tool_call.parameters, indent=2, ensure_ascii=False)}")
            
            result = await self.tool_registry.execute_tool(tool_call)
            
            if result.success:
                print(f"✅ 成功: {json.dumps(result.result, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 失败: {result.error}")
        
        # 显示统计信息
        print("\n" + "=" * 50)
        print("📊 执行统计")
        stats = self.tool_registry.get_statistics()
        print(f"总工具数: {stats['total_tools']}")
        print(f"总调用次数: {stats['total_calls']}")
        print(f"成功率: {stats['success_rate']:.2%}")
        
        # 显示工具文档
        print("\n" + "=" * 50)
        print("📚 工具文档")
        for tool_name in ["write_file", "calculate"]:
            doc = self.tool_registry.get_tool_documentation(tool_name)
            if doc:
                print(f"\n🔧 {doc['name']}")
                print(f"描述: {doc['description']}")
                print(f"类别: {doc['category']}")
                print(f"安全级别: {doc['security_level']}")
                print(f"调用统计: {doc['stats']}")

async def main():
    """主函数"""
    agent = ExampleToolAgent()
    await agent.test_tools()

if __name__ == "__main__":
    asyncio.run(main())