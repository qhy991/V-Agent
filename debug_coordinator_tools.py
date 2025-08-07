#!/usr/bin/env python3
"""
调试协调器工具调用问题
"""

import json
import re

def analyze_coordinator_response(response_text):
    """分析协调器响应，检查工具调用"""
    print("🔍 分析协调器响应...")
    print(f"📝 响应长度: {len(response_text)} 字符")
    print(f"📋 响应内容:")
    print("=" * 50)
    print(response_text)
    print("=" * 50)
    
    # 提取JSON内容
    json_content = extract_json_from_response(response_text)
    if json_content:
        print(f"✅ 找到JSON内容: {len(json_content)} 字符")
        try:
            data = json.loads(json_content)
            print(f"✅ JSON解析成功")
            print(f"📋 JSON结构: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if "tool_calls" in data:
                tool_calls = data["tool_calls"]
                print(f"🔧 找到 {len(tool_calls)} 个工具调用:")
                for i, call in enumerate(tool_calls):
                    print(f"   {i+1}. {call.get('tool_name', 'unknown')} -> {call.get('parameters', {})}")
                    
                    # 特别检查assign_task_to_agent调用
                    if call.get('tool_name') == 'assign_task_to_agent':
                        params = call.get('parameters', {})
                        print(f"      🎯 任务分配调用:")
                        print(f"      - 智能体: {params.get('agent_id')}")
                        print(f"      - 任务描述: {params.get('task_description', '')[:100]}...")
                        print(f"      - 任务类型: {params.get('task_type')}")
            else:
                print("❌ 未找到tool_calls字段")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
    else:
        print("❌ 未找到JSON内容")

def extract_json_from_response(response: str) -> str:
    """从响应中提取JSON内容"""
    if not response:
        return ""
    
    # 尝试多种方法提取JSON
    patterns = [
        r'```json\s*\n(.*?)\n```',           # 标准JSON代码块
        r'```\s*\n(\{.*?\})\s*\n```',        # 简单代码块
        r'(\{.*\})',                         # 直接JSON
        r'```(?:json)?\s*(\{.*?\})\s*```'    # 灵活匹配
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        if matches:
            json_content = matches[0].strip()
            # 验证是否是有效JSON
            try:
                json.loads(json_content)
                return json_content
            except json.JSONDecodeError:
                continue
    
    return ""

def test_task_filtering():
    """测试任务描述过滤"""
    print("\n🧪 测试任务描述过滤...")
    
    # 模拟问题场景中的任务描述
    problematic_task = "设计一个名为counter的Verilog模块，包含完整的端口定义、功能实现和测试台"
    
    # 模拟过滤逻辑（简化版）
    def filter_for_verilog_agent(task_desc):
        original = task_desc
        
        # 移除测试台相关内容
        filtered = task_desc.replace("和测试台", "")
        filtered = filtered.replace("、测试台", "")
        filtered = re.sub(r"，包含完整的端口定义、功能实现和测试台", "，包含完整的端口定义和功能实现", filtered)
        
        if "测试台" in original:
            filtered += """

🚨 **重要说明**: 
- 本任务仅要求完成Verilog模块设计和代码生成
- 测试台(testbench)生成和验证工作将由后续的代码审查智能体负责
- 请专注于设计模块的端口定义、功能实现和代码质量"""
        
        return filtered.strip()
    
    print(f"📝 原始任务: {problematic_task}")
    filtered_task = filter_for_verilog_agent(problematic_task)
    print(f"📝 过滤后任务:")
    print("=" * 50)
    print(filtered_task)
    print("=" * 50)
    
    # 检查过滤效果
    task_part = filtered_task.split("🚨 **重要说明**")[0].strip()
    success = "测试台" not in task_part
    print(f"✅ 过滤效果: {'成功' if success else '失败'}")

if __name__ == "__main__":
    print("🔧 协调器工具调用调试器")
    
    # 模拟问题日志中的响应
    test_response_1 = '''```json
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
    
    test_response_2 = '''```json
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
    
    print("\n1️⃣ 分析第一个响应（推荐智能体）:")
    analyze_coordinator_response(test_response_1)
    
    print("\n2️⃣ 分析第二个响应（分配任务）:")
    analyze_coordinator_response(test_response_2)
    
    # 测试任务过滤
    test_task_filtering()
    
    print("\n📊 问题分析:")
    print("1. 第一个响应缺少tool_calls数组结构")
    print("2. 第二个响应格式正确，应该能被正确解析和执行")
    print("3. 如果第二个响应没有被执行，可能是Function Calling机制的问题")
    print("4. 建议检查BaseAgent的process_with_function_calling方法的实现")
    
    print("\n💡 修复建议:")
    print("1. 确保协调器的LLM输出使用正确的tool_calls数组格式")
    print("2. 检查协调器的Function Calling工具注册是否正确")
    print("3. 验证assign_task_to_agent工具是否被正确注册和实现")
    print("4. 考虑在协调器中添加更详细的工具执行日志")