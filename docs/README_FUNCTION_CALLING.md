# Function Calling系统

## 概述

这是一个基于输出解析的Function Calling系统，允许智能体通过结构化输出调用工具，而不依赖LLM API的原生function calling功能。

## 核心特性

- **智能工具选择**: LLM根据任务需求自动选择合适的工具
- **结构化输出**: 使用JSON格式确保工具调用的准确性
- **异步执行**: 支持长时间运行的工具（如仿真）
- **结果集成**: 工具执行结果自动集成到对话流程中
- **易于扩展**: 简单的工具注册和调用机制

## 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Client    │───▶│  Output Parser   │───▶│ Tool Registry   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Conversation   │    │  Tool Calls      │    │  Tool Results   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 使用方法

### 1. 创建支持Function Calling的智能体

```python
from agents.real_code_reviewer import RealCodeReviewAgent
from config.config import FrameworkConfig

# 创建配置
config = FrameworkConfig.from_env()

# 创建智能体（自动继承FunctionCallingAgent）
agent = RealCodeReviewAgent(config)
```

### 2. 注册工具

工具在智能体初始化时自动注册。当前支持的工具：

- `generate_testbench`: 为Verilog模块生成测试台
- `run_simulation`: 使用iverilog运行仿真
- `analyze_code_quality`: 分析代码质量

### 3. 构建对话

```python
conversation = [
    {
        "role": "system",
        "content": agent._get_base_system_prompt()
    },
    {
        "role": "user",
        "content": "请分析以下代码的质量：\n\n[代码内容]"
    }
]
```

### 4. 执行对话和工具调用

```python
# 调用LLM
response = await agent._call_llm(conversation)

# 解析工具调用
tool_calls = agent._parse_tool_calls(response)

# 执行工具调用
for tool_call in tool_calls:
    result = await agent._execute_tool_call(tool_call)
    if result.success:
        print(f"工具执行成功: {result.result}")
    else:
        print(f"工具执行失败: {result.error}")
```

## 工具调用格式

LLM需要使用以下JSON格式来调用工具：

```json
{
    "tool_calls": [
        {
            "tool_name": "工具名称",
            "parameters": {
                "参数名": "参数值"
            }
        }
    ]
}
```

## 可用工具

### 1. generate_testbench

为Verilog模块生成测试台。

**参数:**
- `module_code` (string, 必需): 完整的Verilog模块代码
- `test_cases` (array, 可选): 测试用例列表

**返回:**
```json
{
    "success": true,
    "testbench_code": "生成的测试台代码",
    "testbench_file": "测试台文件路径",
    "module_info": "模块信息",
    "message": "测试台生成成功"
}
```

### 2. run_simulation

使用iverilog运行Verilog仿真。

**参数:**
- `module_file` (string, 必需): 模块文件路径
- `testbench_file` (string, 必需): 测试台文件路径

**返回:**
```json
{
    "success": true,
    "simulation_output": "仿真输出",
    "simulation_log": "仿真日志",
    "execution_time": "执行时间",
    "message": "仿真执行成功"
}
```

### 3. analyze_code_quality

分析Verilog代码质量。

**参数:**
- `code` (string, 必需): 要分析的Verilog代码

**返回:**
```json
{
    "success": true,
    "code_quality": {
        "syntax_score": 0.9,
        "design_score": 0.8,
        "readability_score": 0.85,
        "overall_score": 0.85
    },
    "issues": ["问题列表"],
    "suggestions": ["建议列表"],
    "strengths": ["优点列表"],
    "module_info": "模块信息",
    "message": "代码质量分析完成"
}
```

## 扩展示例

### 添加新工具

1. 在智能体中注册工具：

```python
def _register_tools(self):
    self.tool_registry.register_tool(
        name="my_new_tool",
        func=self._tool_my_new_tool,
        description="我的新工具描述",
        parameters={
            "param1": {
                "type": "string",
                "description": "参数1描述",
                "required": True
            }
        }
    )
```

2. 实现工具方法：

```python
async def _tool_my_new_tool(self, param1: str) -> Dict[str, Any]:
    """工具：我的新工具"""
    try:
        # 工具实现逻辑
        result = await self._do_something(param1)
        
        return {
            "success": True,
            "result": result,
            "message": "工具执行成功"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

3. 更新system prompt：

```python
def _get_base_system_prompt(self) -> str:
    return """...
可用工具：
1. generate_testbench - 为Verilog模块生成测试台
2. run_simulation - 使用iverilog运行仿真
3. analyze_code_quality - 分析代码质量
4. my_new_tool - 我的新工具描述
..."""
```

## 测试

运行测试：

```bash
# 运行完整测试套件
python test_function_calling_system.py

# 运行演示
python example_function_calling_demo.py
```

## 优势

1. **独立性**: 不依赖LLM API的原生function calling
2. **灵活性**: 可以轻松添加和修改工具
3. **可控性**: 完全控制工具的执行逻辑
4. **可扩展性**: 支持复杂的多工具工作流程
5. **调试友好**: 可以详细跟踪工具调用过程

## 注意事项

1. **LLM输出格式**: 确保LLM按照指定格式输出工具调用
2. **错误处理**: 工具执行失败时要有适当的错误处理
3. **异步支持**: 长时间运行的工具应该使用异步实现
4. **参数验证**: 在工具实现中验证输入参数

## 未来改进

- [ ] 支持更复杂的参数类型
- [ ] 添加工具调用链式执行
- [ ] 实现工具调用缓存
- [ ] 添加工具执行时间限制
- [ ] 支持条件工具调用 