#!/usr/bin/env python3
"""
测试ToolCallParser修复 - 验证单工具调用格式解析
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.function_calling.parser import ToolCallParser
import logging

def test_tool_parser_single_tool_call():
    """测试单工具调用格式解析"""
    print("🧪 测试ToolCallParser单工具调用格式解析...")
    
    # 创建解析器
    logger = logging.getLogger("test_tool_parser")
    logger.setLevel(logging.DEBUG)
    parser = ToolCallParser(logger)
    
    # 测试用例1: 单工具调用格式（直接JSON）
    single_tool_response = '''{
    "tool_name": "assign_task_to_agent",
    "parameters": {
        "agent_id": "enhanced_real_verilog_agent",
        "task_description": "设计一个名为counter的Verilog模块，包含完整的端口定义、功能实现，以及对应的测试台代码"
    }
}'''
    
    print("\n📋 测试用例1: 单工具调用格式（直接JSON）")
    tool_calls = parser.parse_tool_calls_from_response(single_tool_response)
    print(f"   解析结果: {len(tool_calls)} 个工具调用")
    for i, tool_call in enumerate(tool_calls):
        print(f"   工具调用 {i}: {tool_call.tool_name}")
        print(f"   参数: {list(tool_call.parameters.keys())}")
    
    # 测试用例2: 单工具调用格式（JSON代码块）
    single_tool_block_response = '''请执行以下工具调用：

```json
{
    "tool_name": "assign_task_to_agent",
    "parameters": {
        "agent_id": "enhanced_real_verilog_agent",
        "task_description": "设计一个名为counter的Verilog模块"
    }
}
```

请确保任务分配成功。'''
    
    print("\n📋 测试用例2: 单工具调用格式（JSON代码块）")
    tool_calls = parser.parse_tool_calls_from_response(single_tool_block_response)
    print(f"   解析结果: {len(tool_calls)} 个工具调用")
    for i, tool_call in enumerate(tool_calls):
        print(f"   工具调用 {i}: {tool_call.tool_name}")
        print(f"   参数: {list(tool_call.parameters.keys())}")
    
    # 测试用例3: 多工具调用格式（tool_calls数组）
    multi_tool_response = '''{
    "tool_calls": [
        {
            "tool_name": "identify_task_type",
            "parameters": {
                "user_request": "设计一个计数器"
            }
        },
        {
            "tool_name": "recommend_agent",
            "parameters": {
                "task_type": "design",
                "task_description": "设计一个计数器"
            }
        }
    ]
}'''
    
    print("\n📋 测试用例3: 多工具调用格式（tool_calls数组）")
    tool_calls = parser.parse_tool_calls_from_response(multi_tool_response)
    print(f"   解析结果: {len(tool_calls)} 个工具调用")
    for i, tool_call in enumerate(tool_calls):
        print(f"   工具调用 {i}: {tool_call.tool_name}")
        print(f"   参数: {list(tool_call.parameters.keys())}")
    
    # 测试用例4: 无效格式
    invalid_response = '''{
    "message": "这是一个普通消息，不包含工具调用"
}'''
    
    print("\n📋 测试用例4: 无效格式")
    tool_calls = parser.parse_tool_calls_from_response(invalid_response)
    print(f"   解析结果: {len(tool_calls)} 个工具调用")
    
    print("\n" + "="*60)
    print("🏁 测试完成")

if __name__ == "__main__":
    test_tool_parser_single_tool_call() 