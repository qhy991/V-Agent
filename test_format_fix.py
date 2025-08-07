#!/usr/bin/env python3
"""
测试协调器格式修复机制
"""

import json
import re

def extract_json_from_response(response: str) -> str:
    """从响应中提取JSON内容"""
    if not response:
        return ""
    
    patterns = [
        r'```json\s*\n(.*?)\n```',
        r'```\s*\n(\{.*?\})\s*\n```', 
        r'(\{.*\})',
        r'```(?:json)?\s*(\{.*?\})\s*```'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        if matches:
            json_content = matches[0].strip()
            try:
                json.loads(json_content)
                return json_content
            except json.JSONDecodeError:
                continue
    
    return ""

def fix_tool_call_format(result: str) -> str:
    """修复工具调用格式"""
    if not isinstance(result, str) or not result.strip():
        return result
    
    json_content = extract_json_from_response(result.strip())
    if not json_content:
        return result
    
    try:
        data = json.loads(json_content)
        
        # 检查是否是错误的单个工具格式
        if "tool_name" in data and "parameters" in data and "tool_calls" not in data:
            print(f"🔧 检测到错误的单工具格式，自动修复为tool_calls数组格式")
            
            # 转换为正确的格式
            fixed_data = {
                "tool_calls": [
                    {
                        "tool_name": data["tool_name"],
                        "parameters": data["parameters"]
                    }
                ]
            }
            
            # 生成修复后的响应
            fixed_json = json.dumps(fixed_data, ensure_ascii=False, indent=2)
            fixed_result = f"```json\n{fixed_json}\n```"
            
            print(f"✅ 已修复工具调用格式：{data['tool_name']}")
            return fixed_result
        
    except json.JSONDecodeError:
        print("JSON解析失败，保持原始格式")
    
    return result

def test_format_fixes():
    """测试格式修复"""
    print("🧪 测试协调器格式修复机制...")
    
    # 测试用例1：错误格式（日志中的实际问题格式）
    wrong_format = '''```json
{
    "tool_name": "recommend_agent",
    "parameters": {
        "task_type": "verification",
        "task_description": "为counter模块生成测试台并进行验证",
        "priority": "medium",
        "constraints": []
    }
}
```'''
    
    # 测试用例2：正确格式
    correct_format = '''```json
{
    "tool_calls": [
        {
            "tool_name": "assign_task_to_agent",
            "parameters": {
                "agent_id": "enhanced_real_code_review_agent",
                "task_description": "为counter模块生成测试台并进行验证",
                "expected_output": "生成测试台文件并执行验证",
                "task_type": "verification",
                "priority": "medium"
            }
        }
    ]
}
```'''
    
    print("\n1️⃣ 测试错误格式修复：")
    print("原始格式:")
    print(wrong_format[:100] + "...")
    fixed = fix_tool_call_format(wrong_format)
    print("\n修复后格式:")
    print(fixed[:200] + "...")
    
    print("\n2️⃣ 测试正确格式保持不变：")
    print("原始格式:")
    print(correct_format[:100] + "...")
    unchanged = fix_tool_call_format(correct_format)
    print(f"是否保持不变: {'✅ 是' if unchanged == correct_format else '❌ 否'}")
    
    # 验证修复后的格式是否正确
    print("\n3️⃣ 验证修复后的格式：")
    try:
        fixed_json = extract_json_from_response(fixed)
        fixed_data = json.loads(fixed_json)
        
        has_tool_calls = "tool_calls" in fixed_data
        has_valid_structure = (has_tool_calls and 
                              isinstance(fixed_data["tool_calls"], list) and 
                              len(fixed_data["tool_calls"]) > 0 and
                              "tool_name" in fixed_data["tool_calls"][0])
        
        print(f"包含tool_calls数组: {'✅ 是' if has_tool_calls else '❌ 否'}")
        print(f"结构正确: {'✅ 是' if has_valid_structure else '❌ 否'}")
        
        if has_valid_structure:
            tool_name = fixed_data["tool_calls"][0]["tool_name"]
            print(f"修复后的工具名: {tool_name}")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    
    print("\n✅ 格式修复机制测试完成!")

if __name__ == "__main__":
    test_format_fixes()