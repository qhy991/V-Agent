#!/usr/bin/env python3
"""
增强版多智能体对话可视化工具
提供详细的智能体交互、工具调用和美观的界面展示
"""

import gradio as gr
import json
import time
from datetime import datetime
from pathlib import Path
import re

class EnhancedMultiAgentVisualizer:
    """增强版多智能体可视化器"""
    
    def __init__(self):
        self.conversation_history = []
        self.agent_states = {}
        self.tool_executions = []
        
    def parse_detailed_conversation(self, log_content: str) -> dict:
        """解析详细的对话日志"""
        lines = log_content.split('\n')
        messages = []
        current_timestamp = time.time()
        
        # 智能体颜色映射
        agent_colors = {
            'llm_coordinator_agent': '#4ecdc4',
            'enhanced_real_verilog_agent': '#ff6b6b', 
            'enhanced_real_code_review_agent': '#45b7d1',
            'user': '#95a5a6',
            'system': '#f7dc6f'
        }
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 解析时间戳和智能体信息
            timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2})', line)
            agent_match = re.search(r'Agent\.([^-]+)', line)
            
            if timestamp_match and agent_match:
                timestamp = timestamp_match.group(1)
                agent_id = agent_match.group(1)
                
                # 查找工具调用
                if 'tool_calls' in line and '[' in line:
                    tool_match = re.search(r'"tool_name":\s*"([^"]+)"', line)
                    if tool_match:
                        tool_name = tool_match.group(1)
                        
                        # 提取参数信息
                        params_content = self._extract_json_block(lines, i)
                        
                        messages.append({
                            'timestamp': timestamp,
                            'agent_id': agent_id,
                            'type': 'tool_call',
                            'content': f"🔧 调用工具: {tool_name}",
                            'tool_info': {
                                'tool_name': tool_name,
                                'parameters': self._parse_parameters(params_content),
                                'success': True,
                                'result': '执行成功'
                            },
                            'color': agent_colors.get(agent_id, '#bdc3c7')
                        })
                
                # 查找Assistant响应
                elif 'role=assistant' in line:
                    # 查找JSON响应
                    json_content = self._extract_json_block(lines, i)
                    if json_content:
                        messages.append({
                            'timestamp': timestamp,
                            'agent_id': agent_id,
                            'type': 'assistant_response',
                            'content': f"🤖 {agent_id} 响应",
                            'json_content': json_content,
                            'color': agent_colors.get(agent_id, '#bdc3c7')
                        })
                
                # 查找用户消息
                elif 'role=user' in line:
                    user_content = self._extract_user_content(lines, i)
                    if user_content:
                        messages.append({
                            'timestamp': timestamp,
                            'agent_id': 'user',
                            'type': 'user_prompt',
                            'content': user_content,
                            'color': agent_colors['user']
                        })
                
                # 查找系统消息
                elif 'role=system' in line:
                    system_content = self._extract_system_content(lines, i)
                    if system_content:
                        messages.append({
                            'timestamp': timestamp,
                            'agent_id': 'system',
                            'type': 'system_prompt',
                            'content': system_content,
                            'color': agent_colors['system']
                        })
            
            # 查找工具执行结果
            elif '✅ 工具' in line and '执行成功' in line:
                tool_result_match = re.search(r'✅ 工具 (\d+): ([^-]+) - 执行成功', line)
                if tool_result_match:
                    tool_num = tool_result_match.group(1)
                    tool_name = tool_result_match.group(2).strip()
                    
                    result_content = self._extract_result_content(lines, i)
                    
                    messages.append({
                        'timestamp': timestamp_match.group(1) if timestamp_match else '10:12:44',
                        'agent_id': 'llm_coordinator_agent',
                        'type': 'tool_result',
                        'content': f"✅ 工具 {tool_num}: {tool_name} 执行成功",
                        'result_details': result_content,
                        'color': '#4ecdc4'
                    })
            
            i += 1
        
        return {
            'messages': messages,
            'agent_colors': agent_colors,
            'total_messages': len(messages)
        }
    
    def _extract_json_block(self, lines: list, start_idx: int) -> str:
        """提取JSON块"""
        content = ""
        brace_count = 0
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            content += line + "\n"
            brace_count += line.count('{') - line.count('}')
            
            if brace_count <= 0 and '}' in line:
                break
            i += 1
        
        return content.strip()
    
    def _parse_parameters(self, json_content: str) -> dict:
        """解析参数"""
        try:
            # 提取parameters部分
            params_match = re.search(r'"parameters":\s*({[^}]+})', json_content)
            if params_match:
                params_str = params_match.group(1)
                # 简化显示
                return {
                    'task_type': re.search(r'"task_type":\s*"([^"]+)"', params_str),
                    'agent_id': re.search(r'"agent_id":\s*"([^"]+)"', params_str),
                    'task_description': re.search(r'"task_description":\s*"([^"]+)"', params_str)
                }
        except:
            pass
        return {}
    
    def _extract_user_content(self, lines: list, start_idx: int) -> str:
        """提取用户内容"""
        content = ""
        i = start_idx
        
        while i < len(lines) and i < start_idx + 5:
            if '内容前100字:' in lines[i]:
                content = lines[i].split('内容前100字:')[-1].strip()
                break
            i += 1
        
        return content or "用户请求"
    
    def _extract_system_content(self, lines: list, start_idx: int) -> str:
        """提取系统内容"""
        content = ""
        i = start_idx
        
        while i < len(lines) and i < start_idx + 5:
            if '内容前100字:' in lines[i]:
                content = lines[i].split('内容前100字:')[-1].strip()
                break
            i += 1
        
        return content or "系统提示"
    
    def _extract_result_content(self, lines: list, start_idx: int) -> str:
        """提取结果内容"""
        content = ""
        i = start_idx
        
        while i < len(lines) and i < start_idx + 3:
            if '**执行结果**' in lines[i]:
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('**'):
                    content += lines[i] + "\n"
                    i += 1
                break
            i += 1
        
        return content.strip() or "执行成功"
    
    def format_enhanced_message(self, message: dict) -> str:
        """格式化增强消息显示"""
        timestamp = message.get('timestamp', '')
        agent_id = message.get('agent_id', 'unknown')
        msg_type = message.get('type', 'unknown')
        content = message.get('content', '')
        color = message.get('color', '#bdc3c7')
        
        # 智能体图标映射
        agent_icons = {
            'llm_coordinator_agent': '🧠',
            'enhanced_real_verilog_agent': '🔧',
            'enhanced_real_code_review_agent': '🔍',
            'user': '👤',
            'system': '⚙️'
        }
        
        icon = agent_icons.get(agent_id, '🤖')
        
        if msg_type == 'tool_call':
            tool_info = message.get('tool_info', {})
            tool_name = tool_info.get('tool_name', 'unknown')
            parameters = tool_info.get('parameters', {})
            
            return f"""
<div style="border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background: linear-gradient(135deg, {color}10, {color}05); border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <span style="font-size: 1.2em; margin-right: 8px;">{icon}</span>
        <div style="font-weight: bold; color: {color}; font-size: 1.1em;">{agent_id.replace('_', ' ').title()}</div>
        <div style="margin-left: auto; font-size: 0.9em; color: #666;">{timestamp}</div>
    </div>
    <div style="background: {color}15; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
        <div style="font-weight: bold; color: {color}; margin-bottom: 5px;">🔧 工具调用: {tool_name}</div>
        <details style="margin-top: 8px;">
            <summary style="cursor: pointer; color: #666; font-weight: bold;">📋 查看参数详情</summary>
            <pre style="background: #f8f9fa; padding: 8px; border-radius: 4px; margin-top: 5px; font-size: 0.85em; overflow-x: auto;">{json.dumps(parameters, indent=2, ensure_ascii=False)}</pre>
        </details>
    </div>
    <div style="font-size: 0.9em; color: #666;">{content}</div>
</div>
"""
        
        elif msg_type == 'tool_result':
            result_details = message.get('result_details', '')
            
            return f"""
<div style="border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background: linear-gradient(135deg, #4ecdc415, #4ecdc405); border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <span style="font-size: 1.2em; margin-right: 8px;">✅</span>
        <div style="font-weight: bold; color: {color}; font-size: 1.1em;">{agent_id.replace('_', ' ').title()}</div>
        <div style="margin-left: auto; font-size: 0.9em; color: #666;">{timestamp}</div>
    </div>
    <div style="background: #4ecdc415; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
        <div style="font-weight: bold; color: #4ecdc4; margin-bottom: 5px;">{content}</div>
        {f'<div style="font-size: 0.85em; margin-top: 5px;">{result_details}</div>' if result_details else ''}
    </div>
</div>
"""
        
        elif msg_type == 'assistant_response':
            json_content = message.get('json_content', '')
            
            return f"""
<div style="border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background: linear-gradient(135deg, {color}10, {color}05); border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <span style="font-size: 1.2em; margin-right: 8px;">{icon}</span>
        <div style="font-weight: bold; color: {color}; font-size: 1.1em;">{agent_id.replace('_', ' ').title()}</div>
        <div style="margin-left: auto; font-size: 0.9em; color: #666;">{timestamp}</div>
    </div>
    <div style="background: {color}15; padding: 10px; border-radius: 6px;">
        <div style="font-weight: bold; color: {color}; margin-bottom: 5px;">{content}</div>
        <details style="margin-top: 8px;">
            <summary style="cursor: pointer; color: #666; font-weight: bold;">📄 查看JSON响应</summary>
            <pre style="background: #f8f9fa; padding: 8px; border-radius: 4px; margin-top: 5px; font-size: 0.8em; overflow-x: auto; max-height: 200px; overflow-y: auto;">{json_content}</pre>
        </details>
    </div>
</div>
"""
        
        else:
            return f"""
<div style="border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background: linear-gradient(135deg, {color}10, {color}05); border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <span style="font-size: 1.2em; margin-right: 8px;">{icon}</span>
        <div style="font-weight: bold; color: {color}; font-size: 1.1em;">{agent_id.replace('_', ' ').title()}</div>
        <div style="margin-left: auto; font-size: 0.9em; color: #666;">{timestamp}</div>
    </div>
    <div style="font-size: 0.95em; line-height: 1.5;">{content}</div>
</div>
"""
    
    def get_agent_status_display(self, messages: list) -> str:
        """获取智能体状态显示"""
        agents = {}
        
        for msg in messages:
            agent_id = msg.get('agent_id', 'unknown')
            if agent_id not in agents:
                agents[agent_id] = {
                    'count': 0,
                    'last_active': msg.get('timestamp', ''),
                    'types': set()
                }
            agents[agent_id]['count'] += 1
            agents[agent_id]['types'].add(msg.get('type', ''))
        
        status_html = "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;'>"
        
        for agent_id, info in agents.items():
            # 智能体颜色
            agent_colors = {
                'llm_coordinator_agent': '#4ecdc4',
                'enhanced_real_verilog_agent': '#ff6b6b',
                'enhanced_real_code_review_agent': '#45b7d1',
                'user': '#95a5a6',
                'system': '#f7dc6f'
            }
            color = agent_colors.get(agent_id, '#bdc3c7')
            
            # 智能体图标
            agent_icons = {
                'llm_coordinator_agent': '🧠',
                'enhanced_real_verilog_agent': '🔧',
                'enhanced_real_code_review_agent': '🔍',
                'user': '👤',
                'system': '⚙️'
            }
            icon = agent_icons.get(agent_id, '🤖')
            
            status_html += f"""
<div style="border: 2px solid {color}; padding: 15px; border-radius: 12px; text-align: center; background: linear-gradient(135deg, {color}10, {color}05); box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <div style="font-size: 1.5em; margin-bottom: 8px;">{icon}</div>
    <div style="font-weight: bold; color: {color}; font-size: 1.1em; margin-bottom: 5px;">{agent_id.replace('_', ' ').title()}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 8px;">消息数: {info['count']}</div>
    <div style="font-size: 0.8em; color: #888;">最后活跃: {info['last_active']}</div>
    <div style="margin-top: 8px; font-size: 0.8em; color: #666;">
        类型: {', '.join(list(info['types'])[:3])}{'...' if len(info['types']) > 3 else ''}
    </div>
</div>
"""
        
        status_html += "</div>"
        return status_html
    
    def get_statistics_display(self, messages: list) -> str:
        """获取统计信息显示"""
        stats = {
            '总消息数': len(messages),
            '工具调用': len([m for m in messages if m['type'] == 'tool_call']),
            '工具结果': len([m for m in messages if m['type'] == 'tool_result']),
            'Assistant响应': len([m for m in messages if m['type'] == 'assistant_response']),
            '用户消息': len([m for m in messages if m['type'] == 'user_prompt']),
            '系统消息': len([m for m in messages if m['type'] == 'system_prompt'])
        }
        
        # 智能体统计
        agent_stats = {}
        for msg in messages:
            agent_id = msg.get('agent_id', 'unknown')
            if agent_id not in agent_stats:
                agent_stats[agent_id] = 0
            agent_stats[agent_id] += 1
        
        stats_html = f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; margin: 20px 0; color: white;">
    <h3 style="margin: 0 0 15px 0; text-align: center;">📊 对话统计概览</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 20px;">
        {' '.join([f'<div style="text-align: center; padding: 10px; background: rgba(255,255,255,0.2); border-radius: 8px;"><div style="font-size: 1.2em; font-weight: bold;">{v}</div><div style="font-size: 0.9em;">{k}</div></div>' for k, v in stats.items()])}
    </div>
    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
        <h4 style="margin: 0 0 10px 0;">🤖 智能体活跃度</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
            {' '.join([f'<div style="text-align: center; padding: 8px; background: rgba(255,255,255,0.15); border-radius: 6px;"><div style="font-weight: bold;">{agent_id.replace("_", " ").title()}</div><div>{count} 条消息</div></div>' for agent_id, count in agent_stats.items()])}
        </div>
    </div>
</div>
"""
        
        return stats_html

# 创建可视化器实例
visualizer = EnhancedMultiAgentVisualizer()

def create_enhanced_interface():
    """创建增强版界面"""
    
    with gr.Blocks(
        title="增强版多智能体对话可视化工具",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1400px !important;
        }
        .conversation-display {
            max-height: 700px;
            overflow-y: auto;
            padding: 20px;
            background: #fafafa;
            border-radius: 12px;
        }
        """
    ) as demo:
        
        gr.Markdown("""
        # 🎨 增强版多智能体对话可视化工具
        
        ## ✨ 特性
        - 🎯 **清晰的智能体标识**：每个智能体都有独特的图标和颜色
        - 🔧 **详细的工具调用**：显示工具名称、参数和执行结果
        - 📊 **实时统计信息**：智能体活跃度和消息类型统计
        - 🎨 **美观的界面设计**：渐变背景、阴影效果和响应式布局
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                # 输入区域
                gr.Markdown("## 📝 输入日志内容")
                log_input = gr.Textbox(
                    label="粘贴您的对话日志",
                    placeholder="将counter_test_utf8_fixed-806.txt的内容粘贴到这里...",
                    lines=10
                )
                
                with gr.Row():
                    parse_btn = gr.Button("🔍 解析并可视化", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ 清空", variant="secondary")
                
                # 示例数据
                gr.Markdown("### 💡 使用说明")
                gr.Markdown("""
                1. 将您的 `counter_test_utf8_fixed-806.txt` 文件内容复制
                2. 粘贴到上方的输入框中
                3. 点击"解析并可视化"按钮
                4. 查看美观的对话流程展示
                """)
                
            with gr.Column(scale=2):
                # 智能体状态
                gr.Markdown("## 🤖 智能体状态")
                agent_status = gr.HTML(value="<p style='text-align: center; color: #666; padding: 50px;'>等待输入日志内容...</p>")
        
        # 统计信息
        gr.Markdown("## 📊 统计信息")
        stats_display = gr.HTML(value="")
        
        # 对话显示区域
        gr.Markdown("## 💬 对话流程可视化")
        conversation_display = gr.HTML(
            value="<p style='text-align: center; color: #666; padding: 50px;'>点击'解析并可视化'查看对话流程</p>",
            elem_classes=["conversation-display"]
        )
        
        # 事件处理
        def handle_parse(log_content):
            if not log_content.strip():
                return "❌ 请输入日志内容", "", ""
            
            try:
                # 解析日志
                parsed_data = visualizer.parse_detailed_conversation(log_content)
                messages = parsed_data['messages']
                
                if not messages:
                    return "❌ 未找到有效的对话内容", "", ""
                
                # 生成可视化
                conversation_html = ""
                for msg in messages:
                    conversation_html += visualizer.format_enhanced_message(msg)
                
                # 生成智能体状态
                agent_status_html = visualizer.get_agent_status_display(messages)
                
                # 生成统计信息
                stats_html = visualizer.get_statistics_display(messages)
                
                return conversation_html, agent_status_html, stats_html
                
            except Exception as e:
                error_msg = f"❌ 解析失败: {str(e)}"
                return error_msg, "", ""
        
        def handle_clear():
            return "", "", ""
        
        # 绑定事件
        parse_btn.click(
            fn=handle_parse,
            inputs=[log_input],
            outputs=[conversation_display, agent_status, stats_display]
        )
        
        clear_btn.click(
            fn=handle_clear,
            outputs=[log_input, conversation_display, agent_status, stats_display]
        )
        
        # 使用说明
        gr.Markdown("""
        ## 🎯 可视化特性说明
        
        ### 🎨 颜色编码
        - 🧠 **青色**：协调智能体 (llm_coordinator_agent)
        - 🔧 **红色**：Verilog设计智能体 (enhanced_real_verilog_agent)
        - 🔍 **蓝色**：代码审查智能体 (enhanced_real_code_review_agent)
        - 👤 **灰色**：用户消息
        - ⚙️ **黄色**：系统消息
        
        ### 🔧 工具调用展示
        - 显示工具名称和参数
        - 可展开查看详细参数
        - 显示执行结果和状态
        
        ### 📊 统计信息
        - 消息类型统计
        - 智能体活跃度
        - 时间线分析
        """)
    
    return demo

def find_available_port(start_port=8080, max_attempts=10):
    """自动寻找可用端口"""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    print("🚀 启动增强版多智能体对话可视化工具...")
    
    # 自动寻找可用端口
    available_port = find_available_port()
    if available_port is None:
        print("❌ 无法找到可用端口，请手动指定GRADIO_SERVER_PORT环境变量")
        exit(1)
    
    print(f"🔧 使用端口: {available_port}")
    
    # 创建界面
    demo = create_enhanced_interface()
    
    try:
        demo.launch(
            server_name="127.0.0.1",
            server_port=available_port,
            share=False,
            debug=False,
            show_error=True,
            quiet=True
        )
    except KeyboardInterrupt:
        print("\n👋 可视化工具已停止") 