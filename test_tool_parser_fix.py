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
    
    # 🆕 测试用例3: 从日志中提取的实际JSON格式
    log_json_response = '''```json
{
    "tool_name": "write_file",
    "parameters": {
        "file_path": "/Users/haiyan-mini/Documents/Study/V-Agent/experiments/design_counter_20250807_185815/designs/counter.v",
        "content": "module counter (\n    input      clk,\n    input      rst_n,\n    input      en,\n    output reg [3:0] count\n);\n\nalways @(posedge clk or negedge rst_n) begin\n    if (!rst_n) begin\n        count <= 4'b0;\n    end else if (en) begin\n        count <= count + 1;\n    end\nend\n\nendmodule"
    }
}
```'''
    
    print("\n📋 测试用例3: 从日志中提取的实际JSON格式")
    print(f"   响应长度: {len(log_json_response)}")
    print(f"   响应前100字符: {log_json_response[:100]}...")
    print(f"   响应后100字符: {log_json_response[-100:]}...")
    
    # 启用详细调试
    logger.setLevel(logging.DEBUG)
    tool_calls = parser.parse_tool_calls_from_response(log_json_response)
    print(f"   解析结果: {len(tool_calls)} 个工具调用")
    for i, tool_call in enumerate(tool_calls):
        print(f"   工具调用 {i}: {tool_call.tool_name}")
        print(f"   参数: {list(tool_call.parameters.keys())}")
        if "file_path" in tool_call.parameters:
            print(f"   文件路径: {tool_call.parameters['file_path']}")
    
    # 如果解析失败，尝试手动解析
    if len(tool_calls) == 0:
        print("   🔍 手动解析尝试...")
        import re
        import json
        
        # 尝试提取JSON代码块
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, log_json_response, re.DOTALL)
        print(f"   找到 {len(matches)} 个JSON代码块")
        
        for i, match in enumerate(matches):
            print(f"   JSON代码块 {i} 长度: {len(match)}")
            print(f"   JSON代码块 {i} 前100字符: {match[:100]}...")
            try:
                data = json.loads(match)
                print(f"   JSON解析成功，顶级键: {list(data.keys())}")
                if 'tool_name' in data:
                    print(f"   找到工具名称: {data['tool_name']}")
            except json.JSONDecodeError as e:
                print(f"   JSON解析失败: {str(e)}")
    
    # 🆕 测试用例4: 直接JSON格式（不带代码块）
    direct_json_response = '''{
    "tool_name": "write_file",
    "parameters": {
        "file_path": "/Users/haiyan-mini/Documents/Study/V-Agent/experiments/design_counter_20250807_185815/designs/counter.v",
        "content": "module counter (input clk, input rst_n, input en, output reg [3:0] count); always @(posedge clk or negedge rst_n) begin if (!rst_n) count <= 4'b0; else if (en) count <= count + 1; end endmodule"
    }
}'''
    
    print("\n📋 测试用例4: 直接JSON格式（不带代码块）")
    tool_calls = parser.parse_tool_calls_from_response(direct_json_response)
    print(f"   解析结果: {len(tool_calls)} 个工具调用")
    for i, tool_call in enumerate(tool_calls):
        print(f"   工具调用 {i}: {tool_call.tool_name}")
        print(f"   参数: {list(tool_call.parameters.keys())}")
    
    print("\n✅ 所有测试用例完成")

if __name__ == "__main__":
    test_tool_parser_single_tool_call() 