#!/usr/bin/env python3
"""
简单的可视化功能测试（不依赖Gradio）
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class SimpleVisualizer:
    """简单的对话可视化器"""
    
    def __init__(self):
        self.conversation_history = []
        self.agent_states = {}
    
    def format_message_display(self, message: Dict[str, Any]) -> str:
        """格式化消息显示为HTML"""
        timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
        agent_id = message.get('agent_id', 'unknown')
        msg_type = message.get('type', message.get('role', 'unknown'))
        content = message.get('content', '')
        
        # 根据消息类型设置不同的样式
        if msg_type in ['system_prompt', 'system']:
            return f"""
<div style="border-left: 4px solid #ff6b6b; padding: 10px; margin: 5px 0; background: #fff5f5;">
    <div style="font-weight: bold; color: #ff6b6b;">🔧 System - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <div style="font-size: 0.9em;">{content[:200]}{'...' if len(content) > 200 else ''}</div>
</div>
"""
        elif msg_type in ['user_prompt', 'user']:
            return f"""
<div style="border-left: 4px solid #4ecdc4; padding: 10px; margin: 5px 0; background: #f0fdfc;">
    <div style="font-weight: bold; color: #4ecdc4;">👤 User - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <div style="font-size: 0.9em;">{content}</div>
</div>
"""
        elif msg_type == 'tool_call':
            tool_info = message.get('tool_info', {})
            tool_name = tool_info.get('tool_name', 'unknown')
            success = tool_info.get('success', False)
            status_color = "#45b7d1" if success else "#ff6b6b"
            status_bg = "#f0f9ff" if success else "#fff5f5"
            status_icon = "✅" if success else "⚙️"
            
            return f"""
<div style="border-left: 4px solid {status_color}; padding: 10px; margin: 5px 0; background: {status_bg};">
    <div style="font-weight: bold; color: {status_color};">{status_icon} Tool Call - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <div style="font-weight: bold; margin-bottom: 5px;">🔧 {tool_name}</div>
    <div style="font-size: 0.85em;">{content}</div>
</div>
"""
        elif msg_type in ['tool_result']:
            tool_info = message.get('tool_info', {})
            success = tool_info.get('success', False)
            status_color = "#45b7d1" if success else "#ff6b6b"
            status_bg = "#f0f9ff" if success else "#fff5f5"
            status_icon = "✅" if success else "❌"
            
            return f"""
<div style="border-left: 4px solid {status_color}; padding: 10px; margin: 5px 0; background: {status_bg};">
    <div style="font-weight: bold; color: {status_color};">{status_icon} Tool Result - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <div style="font-size: 0.85em;">{content}</div>
</div>
"""
        elif msg_type in ['assistant_response', 'assistant']:
            return f"""
<div style="border-left: 4px solid #95a5a6; padding: 10px; margin: 5px 0; background: #f8f9fa;">
    <div style="font-weight: bold; color: #95a5a6;">🤖 Assistant - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <div style="font-size: 0.9em;">{content}</div>
</div>
"""
        else:
            return f"""
<div style="border-left: 4px solid #bdc3c7; padding: 10px; margin: 5px 0; background: #ecf0f1;">
    <div style="font-weight: bold; color: #7f8c8d;">📝 {msg_type} - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <div style="font-size: 0.9em;">{content}</div>
</div>
"""
    
    def load_conversation_from_json(self, json_file_path: str) -> str:
        """从JSON文件加载对话历史"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 尝试多种路径提取对话历史
            conversation_history = []
            
            if 'experiment_report' in data and 'conversation_history' in data['experiment_report']:
                conversation_history = data['experiment_report']['conversation_history']
            elif 'conversation_history' in data:
                conversation_history = data['conversation_history']
            
            if not conversation_history:
                return f"❌ 未找到对话历史数据"
            
            # 转换消息格式
            self.conversation_history = []
            for msg in conversation_history:
                # 转换消息格式，添加type字段
                formatted_msg = {
                    'timestamp': msg.get('timestamp', time.time()),
                    'agent_id': msg.get('agent_id', 'unknown'),
                    'type': msg.get('role', 'unknown'),  # 使用role作为type
                    'content': msg.get('content', ''),
                }
                
                # 如果有tool_info，也添加进去
                if 'tool_info' in msg:
                    formatted_msg['tool_info'] = msg['tool_info']
                
                self.conversation_history.append(formatted_msg)
            
            return f"✅ 成功加载 {len(conversation_history)} 条对话消息"
            
        except Exception as e:
            return f"❌ 加载失败: {str(e)}"
    
    def generate_html_report(self, output_file: str) -> str:
        """生成HTML报告"""
        try:
            html_content = ""
            for msg in self.conversation_history:
                html_content += self.format_message_display(msg)
            
            # 生成统计信息
            stats = {
                "总消息数": len(self.conversation_history),
                "参与智能体": len(set(msg['agent_id'] for msg in self.conversation_history)),
                "消息类型": {}
            }
            
            # 统计消息类型
            for msg in self.conversation_history:
                msg_type = msg['type']
                stats["消息类型"][msg_type] = stats["消息类型"].get(msg_type, 0) + 1
            
            stats_html = f"""
<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
    <h3>📊 对话统计</h3>
    <p><strong>总消息数:</strong> {stats['总消息数']}</p>
    <p><strong>参与智能体:</strong> {stats['参与智能体']}</p>
    <p><strong>消息类型分布:</strong></p>
    <ul>
        {' '.join([f'<li>{k}: {v}</li>' for k, v in stats['消息类型'].items()])}
    </ul>
</div>
"""
            
            full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>多智能体对话可视化</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 多智能体对话可视化报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        {stats_html}
        
        <h2>📝 对话流程</h2>
        {html_content}
    </div>
</body>
</html>
"""
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            return f"✅ HTML报告已生成: {output_file}"
            
        except Exception as e:
            return f"❌ 生成报告失败: {str(e)}"

def test_simple_visualization():
    """测试简单可视化功能"""
    print("🧪 开始测试简单可视化功能...")
    
    visualizer = SimpleVisualizer()
    
    # 测试1: 加载成功的对话历史
    print("\n📝 测试1: 加载成功的对话历史")
    test_file = "/Users/haiyan-mini/Documents/Study/V-Agent/test_full_workflow_result.json"
    
    if Path(test_file).exists():
        result = visualizer.load_conversation_from_json(test_file)
        print(f"加载结果: {result}")
        
        if result.startswith("✅"):
            print(f"✅ 成功! 对话历史包含 {len(visualizer.conversation_history)} 条消息")
            
            # 显示消息类型统计
            types = {}
            agents = set()
            for msg in visualizer.conversation_history:
                msg_type = msg['type']
                types[msg_type] = types.get(msg_type, 0) + 1
                agents.add(msg['agent_id'])
            
            print(f"📊 统计信息:")
            print(f"  - 参与智能体: {len(agents)} 个 ({', '.join(agents)})")
            print(f"  - 消息类型分布: {types}")
            
            # 生成HTML报告
            html_file = "/Users/haiyan-mini/Documents/Study/V-Agent/conversation_visualization.html"
            html_result = visualizer.generate_html_report(html_file)
            print(f"HTML报告: {html_result}")
            
        else:
            print(f"❌ 加载失败: {result}")
    else:
        print(f"❌ 测试文件不存在: {test_file}")
    
    # 测试2: 加载失败实验的报告
    print("\n📝 测试2: 加载失败实验的报告")
    failed_report = "/Users/haiyan-mini/Documents/Study/V-Agent/llm_experiments/llm_coordinator_counter_1754404768/reports/experiment_report.json"
    
    if Path(failed_report).exists():
        result = visualizer.load_conversation_from_json(failed_report)
        print(f"加载结果: {result}")
    else:
        print(f"❌ 失败实验报告不存在: {failed_report}")
    
    print("\n🎉 简单可视化功能测试完成!")

if __name__ == "__main__":
    test_simple_visualization()