#!/usr/bin/env python3
"""
改进的counter_test_utf8_fixed-806.txt文件解析器
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path

def parse_counter_test_file(file_path: str) -> dict:
    """解析counter测试文件并生成可视化格式"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 初始化结果
    result = {
        "experiment_id": "counter_test_1754446364",
        "success": True,
        "conversation_history": [],
        "tool_executions": [],
        "agent_interactions": []
    }
    
    lines = content.split('\n')
    current_timestamp = time.time()
    
    # 查找关键部分
    tool_calls = []
    assistant_responses = []
    user_messages = []
    system_messages = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 查找工具调用
        if 'tool_calls' in line and '[' in line:
            # 提取工具调用信息
            tool_match = re.search(r'"tool_name":\s*"([^"]+)"', line)
            if tool_match:
                tool_name = tool_match.group(1)
                
                # 查找参数信息
                params_start = line.find('"parameters"')
                if params_start != -1:
                    # 提取参数部分
                    params_content = ""
                    brace_count = 0
                    j = i
                    while j < len(lines):
                        params_content += lines[j] + "\n"
                        brace_count += lines[j].count('{') - lines[j].count('}')
                        if brace_count <= 0 and '}' in lines[j]:
                            break
                        j += 1
                    
                    # 简化参数显示
                    params_display = f"工具: {tool_name}"
                    if '"task_type"' in params_content:
                        task_match = re.search(r'"task_type":\s*"([^"]+)"', params_content)
                        if task_match:
                            params_display += f", 任务类型: {task_match.group(1)}"
                    
                    tool_calls.append({
                        "timestamp": current_timestamp + len(tool_calls),
                        "agent_id": "llm_coordinator_agent",
                        "type": "tool_call",
                        "content": params_display,
                        "tool_info": {
                            "tool_name": tool_name,
                            "success": True,
                            "result": "执行成功",
                            "parameters": {"tool_name": tool_name}
                        }
                    })
        
        # 查找Assistant响应
        elif line.startswith('Assistant:'):
            response_content = line.replace('Assistant:', '').strip()
            if response_content:
                assistant_responses.append({
                    "timestamp": current_timestamp + len(assistant_responses),
                    "agent_id": "llm_coordinator_agent", 
                    "type": "assistant_response",
                    "content": response_content
                })
        
        # 查找用户消息
        elif '🧠 协调任务' in line:
            user_content = ""
            j = i
            while j < len(lines) and not lines[j].strip().startswith('**任务ID**'):
                user_content += lines[j] + "\n"
                j += 1
            user_messages.append({
                "timestamp": current_timestamp,
                "agent_id": "user",
                "type": "user_prompt", 
                "content": user_content.strip()
            })
        
        # 查找系统消息
        elif '🔧 工具执行结果详细报告' in line:
            system_content = ""
            j = i
            while j < len(lines) and j < i + 10:  # 限制长度
                system_content += lines[j] + "\n"
                j += 1
            system_messages.append({
                "timestamp": current_timestamp + len(system_messages),
                "agent_id": "system",
                "type": "system_prompt",
                "content": system_content.strip()
            })
        
        # 查找工具执行结果
        elif '✅ 工具' in line and '执行成功' in line:
            tool_result_match = re.search(r'✅ 工具 (\d+): ([^-]+) - 执行成功', line)
            if tool_result_match:
                tool_num = tool_result_match.group(1)
                tool_name = tool_result_match.group(2).strip()
                
                # 查找执行结果详情
                result_content = ""
                j = i
                while j < len(lines) and j < i + 5:
                    if '**执行结果**' in lines[j]:
                        j += 1
                        while j < len(lines) and not lines[j].strip().startswith('**'):
                            result_content += lines[j] + "\n"
                            j += 1
                        break
                    j += 1
                
                tool_calls.append({
                    "timestamp": current_timestamp + len(tool_calls),
                    "agent_id": "llm_coordinator_agent",
                    "type": "tool_call",
                    "content": f"工具 {tool_num}: {tool_name}",
                    "tool_info": {
                        "tool_name": tool_name,
                        "success": True,
                        "result": result_content.strip() or "执行成功"
                    }
                })
        
        i += 1
    
    # 合并所有消息
    all_messages = user_messages + system_messages + tool_calls + assistant_responses
    all_messages.sort(key=lambda x: x['timestamp'])
    
    result["conversation_history"] = all_messages
    
    return result

def save_visualization_data(data: dict, output_path: str):
    """保存可视化数据"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 可视化数据已保存到: {output_path}")

if __name__ == "__main__":
    # 解析文件
    input_file = "counter_test_utf8_fixed-806.txt"
    output_file = "experiments/请设计一个名为counter的Ve_1754446364/reports/experiment_report.json"
    
    # 确保输出目录存在
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # 解析并保存
    data = parse_counter_test_file(input_file)
    save_visualization_data(data, output_file)
    
    print(f"📊 解析结果:")
    print(f"- 总消息数: {len(data['conversation_history'])}")
    print(f"- 工具调用数: {len([m for m in data['conversation_history'] if m['type'] == 'tool_call'])}")
    print(f"- Assistant响应数: {len([m for m in data['conversation_history'] if m['type'] == 'assistant_response'])}")
    print(f"- 用户消息数: {len([m for m in data['conversation_history'] if m['type'] == 'user_prompt'])}")
    print(f"- 系统消息数: {len([m for m in data['conversation_history'] if m['type'] == 'system_prompt'])}")
    
    print(f"\n🎯 现在您可以在可视化工具中使用以下路径:")
    print(f"C:\\Users\\84672\\Documents\\Research\\V-Agent\\experiments\\请设计一个名为counter的Ve_1754446364")
    
    # 显示前几个消息的预览
    print(f"\n📝 消息预览:")
    for i, msg in enumerate(data['conversation_history'][:5]):
        print(f"{i+1}. [{msg['type']}] {msg['agent_id']}: {msg['content'][:50]}...") 