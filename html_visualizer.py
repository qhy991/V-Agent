#!/usr/bin/env python3
"""
HTML可视化器 - 直接生成HTML文件
HTML Visualizer - Generate HTML files directly
"""

import json
import os
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class HTMLVisualizer:
    def __init__(self):
        self.experiment_id = "llm_coordinator_counter_1754463430"
        self.base_path = Path("llm_experiments") / self.experiment_id
        
    def load_experiment_data(self):
        """加载实验数据"""
        try:
            # 加载实验报告
            report_path = self.base_path / "reports" / "experiment_report.json"
            with open(report_path, 'r', encoding='utf-8') as f:
                self.experiment_report = json.load(f)
            
            # 加载实验摘要
            summary_path = self.base_path / "reports" / "experiment_summary.txt"
            with open(summary_path, 'r', encoding='utf-8') as f:
                self.experiment_summary = f.read()
            
            # 加载设计文件
            design_path = self.base_path / "designs" / "counter_v2.v"
            with open(design_path, 'r', encoding='utf-8') as f:
                self.design_code = f.read()
            
            # 加载测试台文件
            testbench_path = self.base_path / "testbenches" / "testbench_counter.v"
            with open(testbench_path, 'r', encoding='utf-8') as f:
                self.testbench_code = f.read()
            
            # 加载日志文件
            log_file = "counter_test_utf8_fixed_20250806_145707.txt"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    self.log_data = f.read()
            else:
                self.log_data = "日志文件不存在"
                
            return True
        except Exception as e:
            print(f"加载实验数据失败: {e}")
            return False
    
    def parse_conversation_data(self):
        """解析对话数据"""
        conversation_data = []
        
        # 从实验报告中提取对话历史
        detailed_result = self.experiment_report.get('detailed_result', {})
        conversation_history = detailed_result.get('conversation_history', [])
        
        for msg in conversation_history:
            timestamp = msg.get('timestamp', 0)
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            agent_id = msg.get('agent_id', 'unknown')
            
            # 转换时间戳为可读格式
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = f"{timestamp:.1f}"
            else:
                time_str = "N/A"
            
            conversation_data.append({
                'time': time_str,
                'role': role,
                'agent_id': agent_id,
                'content': content[:500] + '...' if len(content) > 500 else content,
                'full_content': content
            })
        
        return conversation_data
    
    def parse_log_conversations(self):
        """从日志中解析对话内容"""
        log_conversations = []
        
        if not hasattr(self, 'log_data') or self.log_data == "日志文件不存在":
            return log_conversations
        
        lines = self.log_data.split('\n')
        current_conversation = []
        
        for line in lines:
            if 'LLM响应长度:' in line:
                # 提取LLM响应信息
                parts = line.split(' - ')
                if len(parts) >= 3:
                    time_str = parts[0]
                    agent_part = parts[1]
                    response_length = line.split('LLM响应长度: ')[-1].strip()
                    
                    # 查找对应的LLM调用信息
                    for i in range(max(0, len(lines) - 50), len(lines)):
                        if i < len(lines) and '发起LLM调用' in lines[i] and agent_part in lines[i]:
                            llm_call_time = lines[i].split(' - ')[0] if ' - ' in lines[i] else time_str
                            break
                    else:
                        llm_call_time = time_str
                    
                    log_conversations.append({
                        'time': llm_call_time,
                        'agent': agent_part.replace('Agent.', ''),
                        'type': 'LLM调用',
                        'details': f'响应长度: {response_length} 字符',
                        'duration': '约4-6秒'
                    })
            
            elif '工具执行成功:' in line:
                # 提取工具执行信息
                parts = line.split(' - ')
                if len(parts) >= 3:
                    time_str = parts[0]
                    agent_part = parts[1]
                    tool_name = line.split('工具执行成功: ')[-1].strip()
                    
                    log_conversations.append({
                        'time': time_str,
                        'agent': agent_part.replace('Agent.', ''),
                        'type': '工具执行',
                        'details': f'成功执行: {tool_name}',
                        'duration': 'N/A'
                    })
            
            elif '工具执行失败:' in line:
                # 提取工具失败信息
                parts = line.split(' - ')
                if len(parts) >= 3:
                    time_str = parts[0]
                    agent_part = parts[1]
                    tool_name = line.split('工具执行失败: ')[-1].strip()
                    
                    log_conversations.append({
                        'time': time_str,
                        'agent': agent_part.replace('Agent.', ''),
                        'type': '工具失败',
                        'details': f'失败: {tool_name}',
                        'duration': 'N/A'
                    })
        
        return log_conversations
    
    def create_conversation_timeline_chart(self):
        """创建对话时间线图表"""
        conversation_data = self.parse_conversation_data()
        log_conversations = self.parse_log_conversations()
        
        if not conversation_data and not log_conversations:
            return None
        
        fig = go.Figure()
        
        # 添加对话历史数据
        for i, conv in enumerate(conversation_data):
            # 设置颜色
            colors = {
                'user': '#4CAF50',
                'assistant': '#2196F3',
                'system': '#FF9800'
            }
            color = colors.get(conv['role'], '#9E9E9E')
            
            fig.add_trace(go.Scatter(
                x=[conv['time']],
                y=[i],
                mode='markers+text',
                marker=dict(size=12, color=color),
                text=[f"{conv['role']}<br>{conv['agent_id']}"],
                textposition="middle right",
                name=conv['role'],
                hovertemplate=f"<b>{conv['role']}</b><br>" +
                            f"智能体: {conv['agent_id']}<br>" +
                            f"时间: {conv['time']}<br>" +
                            f"内容: {conv['content'][:100]}...<br>" +
                            f"<extra></extra>"
            ))
        
        # 添加日志对话数据
        for i, log_conv in enumerate(log_conversations):
            offset = len(conversation_data) + i
            
            # 设置颜色
            colors = {
                'LLM调用': '#9C27B0',
                '工具执行': '#4CAF50',
                '工具失败': '#F44336'
            }
            color = colors.get(log_conv['type'], '#9E9E9E')
            
            fig.add_trace(go.Scatter(
                x=[log_conv['time']],
                y=[offset],
                mode='markers+text',
                marker=dict(size=10, color=color, symbol='diamond'),
                text=[f"{log_conv['type']}<br>{log_conv['agent']}"],
                textposition="middle right",
                name=log_conv['type'],
                hovertemplate=f"<b>{log_conv['type']}</b><br>" +
                            f"智能体: {log_conv['agent']}<br>" +
                            f"时间: {log_conv['time']}<br>" +
                            f"详情: {log_conv['details']}<br>" +
                            f"<extra></extra>"
            ))
        
        fig.update_layout(
            title="💬 对话时间线",
            xaxis_title="时间",
            yaxis_title="对话事件",
            height=500,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def create_workflow_timeline_chart(self):
        """创建工作流时间线图表"""
        timeline_data = self.experiment_report.get('execution_timeline', [])
        
        if not timeline_data:
            return None
        
        fig = go.Figure()
        
        for i, event in enumerate(timeline_data):
            timestamp = event.get('timestamp', 0)
            event_type = event.get('event_type', 'unknown')
            agent_id = event.get('agent_id', 'unknown')
            description = event.get('description', '')
            
            # 转换时间戳为相对时间（秒）
            relative_time = timestamp - timeline_data[0]['timestamp'] if timeline_data else 0
            
            # 设置颜色
            colors = {
                'agent_completion': '#4CAF50',
                'tool_execution': '#2196F3',
                'error': '#F44336'
            }
            color = colors.get(event_type, '#9E9E9E')
            
            fig.add_trace(go.Scatter(
                x=[relative_time],
                y=[i],
                mode='markers+text',
                marker=dict(size=15, color=color),
                text=[f"{agent_id}<br>{description}"],
                textposition="middle right",
                name=event_type,
                hovertemplate=f"<b>{event_type}</b><br>" +
                            f"智能体: {agent_id}<br>" +
                            f"描述: {description}<br>" +
                            f"时间: {relative_time:.1f}s<br>" +
                            f"<extra></extra>"
            ))
        
        fig.update_layout(
            title="🔄 工作流执行时间线",
            xaxis_title="时间 (秒)",
            yaxis_title="事件",
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def create_agent_performance_chart(self):
        """创建智能体性能图表"""
        agent_interactions = self.experiment_report.get('agent_interactions', [])
        
        if not agent_interactions:
            return None
        
        # 提取数据
        agents = []
        execution_times = []
        response_lengths = []
        
        for interaction in agent_interactions:
            agent_id = interaction.get('target_agent_id', 'unknown')
            execution_time = interaction.get('execution_time', 0)
            response_length = interaction.get('response_length', 0)
            
            agents.append(agent_id)
            execution_times.append(execution_time)
            response_lengths.append(response_length)
        
        # 创建性能对比图
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=agents,
                y=execution_times,
                name='执行时间 (秒)',
                marker_color='#2196F3'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=agents,
                y=response_lengths,
                name='响应长度 (字符)',
                marker_color='#FF9800'
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title="🤖 智能体性能对比",
            xaxis_title="智能体",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        fig.update_yaxes(title_text="执行时间 (秒)", secondary_y=False)
        fig.update_yaxes(title_text="响应长度 (字符)", secondary_y=True)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def create_performance_summary_chart(self):
        """创建性能摘要图表"""
        workflow_stages = self.experiment_report.get('workflow_stages', [])
        
        if not workflow_stages:
            return None
        
        # 提取数据
        stage_names = []
        durations = []
        success_status = []
        
        for stage in workflow_stages:
            stage_name = stage.get('stage_name', 'unknown')
            duration = stage.get('duration', 0)
            success = stage.get('success', False)
            
            stage_names.append(stage_name)
            durations.append(duration)
            success_status.append('成功' if success else '失败')
        
        # 创建饼图
        fig = go.Figure(data=[go.Pie(
            labels=stage_names,
            values=durations,
            hole=0.3,
            textinfo='label+percent',
            textposition='inside'
        )])
        
        fig.update_layout(
            title="📊 工作流阶段时间分布",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def create_error_analysis_chart(self):
        """创建错误分析图表"""
        # 从日志中提取错误信息
        log_file = "counter_test_utf8_fixed_20250806_145707.txt"
        error_types = {
            '编译失败': 0,
            '工具执行失败': 0,
            '语法错误': 0,
            '其他错误': 0
        }
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                if '编译失败' in line:
                    error_types['编译失败'] += 1
                elif '工具执行失败' in line:
                    error_types['工具执行失败'] += 1
                elif 'syntax error' in line.lower():
                    error_types['语法错误'] += 1
                elif 'ERROR' in line:
                    error_types['其他错误'] += 1
        
        # 创建错误统计图
        fig = go.Figure(data=[go.Bar(
            x=list(error_types.keys()),
            y=list(error_types.values()),
            marker_color=['#F44336', '#FF9800', '#FFC107', '#9E9E9E']
        )])
        
        fig.update_layout(
            title="⚠️ 错误类型统计",
            xaxis_title="错误类型",
            yaxis_title="错误次数",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def generate_html_report(self):
        """生成完整的HTML报告"""
        if not self.load_experiment_data():
            return False
        
        # 生成图表
        conversation_chart = self.create_conversation_timeline_chart()
        timeline_chart = self.create_workflow_timeline_chart()
        performance_chart = self.create_agent_performance_chart()
        summary_chart = self.create_performance_summary_chart()
        error_chart = self.create_error_analysis_chart()
        
        # 解析对话数据
        conversation_data = self.parse_conversation_data()
        log_conversations = self.parse_log_conversations()
        
        # 创建对话内容HTML
        conversation_html = ""
        if conversation_data:
            conversation_html += "<h3>📝 对话历史</h3>"
            for conv in conversation_data:
                role_icon = "👤" if conv['role'] == 'user' else "🤖" if conv['role'] == 'assistant' else "⚙️"
                conversation_html += f"""
                <div class="conversation-item">
                    <div class="conversation-header">
                        <span class="role-icon">{role_icon}</span>
                        <span class="role-name">{conv['role'].title()}</span>
                        <span class="agent-id">({conv['agent_id']})</span>
                        <span class="time">{conv['time']}</span>
                    </div>
                    <div class="conversation-content">
                        <pre>{conv['content']}</pre>
                    </div>
                </div>
                """
        
        if log_conversations:
            conversation_html += "<h3>📋 交互记录</h3>"
            for log_conv in log_conversations:
                type_icon = "🧠" if log_conv['type'] == 'LLM调用' else "🔧" if log_conv['type'] == '工具执行' else "❌"
                conversation_html += f"""
                <div class="conversation-item">
                    <div class="conversation-header">
                        <span class="role-icon">{type_icon}</span>
                        <span class="role-name">{log_conv['type']}</span>
                        <span class="agent-id">({log_conv['agent']})</span>
                        <span class="time">{log_conv['time']}</span>
                    </div>
                    <div class="conversation-content">
                        <p>{log_conv['details']}</p>
                    </div>
                </div>
                """
        
        # 创建HTML内容
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V-Agent 实验可视化报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 25px;
            border-radius: 10px;
            background: #f8f9fa;
            border-left: 5px solid #667eea;
        }}
        .section h2 {{
            color: #333;
            margin-top: 0;
            font-size: 1.8em;
        }}
        .overview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .overview-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .overview-card h3 {{
            color: #667eea;
            margin: 0 0 10px 0;
        }}
        .overview-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .overview-card .label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .code-section {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
            margin-bottom: 20px;
        }}
        .code-section h3 {{
            color: #f7fafc;
            margin-top: 0;
        }}
        .file-structure {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            border: 1px solid #dee2e6;
        }}
        .success {{
            color: #28a745;
        }}
        .error {{
            color: #dc3545;
        }}
        .warning {{
            color: #ffc107;
        }}
        .nav-tabs {{
            display: flex;
            border-bottom: 2px solid #dee2e6;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .nav-tab {{
            padding: 10px 20px;
            background: #f8f9fa;
            border: none;
            cursor: pointer;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
            margin-bottom: 5px;
        }}
        .nav-tab.active {{
            background: #667eea;
            color: white;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .conversation-item {{
            background: white;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .conversation-header {{
            background: #f8f9fa;
            padding: 10px 15px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .role-icon {{
            font-size: 1.2em;
        }}
        .role-name {{
            font-weight: bold;
            color: #333;
        }}
        .agent-id {{
            color: #666;
            font-size: 0.9em;
        }}
        .time {{
            margin-left: auto;
            color: #999;
            font-size: 0.8em;
        }}
        .conversation-content {{
            padding: 15px;
        }}
        .conversation-content pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        .conversation-content p {{
            margin: 0;
            line-height: 1.4;
        }}
        @media (max-width: 768px) {{
            .overview-grid {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 2em;
            }}
            .nav-tabs {{
                flex-direction: column;
            }}
            .nav-tab {{
                border-radius: 5px;
                margin-bottom: 2px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 V-Agent 实验可视化报告</h1>
            <p>基于统一日志系统的实验结果可视化展示</p>
            <p>实验ID: {self.experiment_report.get('experiment_id', 'N/A')} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <!-- 实验概览 -->
            <div class="section">
                <h2>📊 实验概览</h2>
                <div class="overview-grid">
                    <div class="overview-card">
                        <h3>执行状态</h3>
                        <div class="value {'success' if self.experiment_report.get('success') else 'error'}">
                            {'✅ 成功' if self.experiment_report.get('success') else '❌ 失败'}
                        </div>
                    </div>
                    <div class="overview-card">
                        <h3>任务耗时</h3>
                        <div class="value">{self.experiment_report.get('task_duration', 0):.2f}s</div>
                        <div class="label">总执行时间</div>
                    </div>
                    <div class="overview-card">
                        <h3>智能体交互</h3>
                        <div class="value">{self.experiment_report.get('agent_interaction_count', 0)}</div>
                        <div class="label">交互次数</div>
                    </div>
                    <div class="overview-card">
                        <h3>工作流阶段</h3>
                        <div class="value">{self.experiment_report.get('workflow_stage_count', 0)}</div>
                        <div class="label">阶段数量</div>
                    </div>
                </div>
            </div>
            
            <!-- 导航标签 -->
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showTab('conversations')">💬 对话内容</button>
                <button class="nav-tab" onclick="showTab('workflow')">🔄 工作流分析</button>
                <button class="nav-tab" onclick="showTab('performance')">📈 性能分析</button>
                <button class="nav-tab" onclick="showTab('code')">💻 代码展示</button>
                <button class="nav-tab" onclick="showTab('errors')">⚠️ 错误分析</button>
                <button class="nav-tab" onclick="showTab('files')">📁 文件结构</button>
            </div>
            
            <!-- 对话内容标签页 -->
            <div id="conversations" class="tab-content active">
                <div class="section">
                    <h2>💬 对话内容分析</h2>
                    <div class="chart-container">
                        {conversation_chart if conversation_chart else '<p>暂无对话数据</p>'}
                    </div>
                </div>
                <div class="section">
                    <h2>📝 详细对话记录</h2>
                    <div class="conversation-list">
                        {conversation_html if conversation_html else '<p>暂无对话记录</p>'}
                    </div>
                </div>
            </div>
            
            <!-- 工作流分析标签页 -->
            <div id="workflow" class="tab-content">
                <div class="section">
                    <h2>🔄 工作流执行时间线</h2>
                    <div class="chart-container">
                        {timeline_chart if timeline_chart else '<p>暂无时间线数据</p>'}
                    </div>
                </div>
            </div>
            
            <!-- 性能分析标签页 -->
            <div id="performance" class="tab-content">
                <div class="section">
                    <h2>🤖 智能体性能对比</h2>
                    <div class="chart-container">
                        {performance_chart if performance_chart else '<p>暂无性能数据</p>'}
                    </div>
                </div>
                <div class="section">
                    <h2>📊 工作流阶段时间分布</h2>
                    <div class="chart-container">
                        {summary_chart if summary_chart else '<p>暂无阶段数据</p>'}
                    </div>
                </div>
            </div>
            
            <!-- 代码展示标签页 -->
            <div id="code" class="tab-content">
                <div class="section">
                    <h2>💻 Verilog设计代码</h2>
                    <div class="code-section">
                        <h3>counter_v2.v</h3>
                        <pre>{self.design_code}</pre>
                    </div>
                </div>
                <div class="section">
                    <h2>🧪 测试台代码</h2>
                    <div class="code-section">
                        <h3>testbench_counter.v</h3>
                        <pre>{self.testbench_code[:1000]}{'...' if len(self.testbench_code) > 1000 else ''}</pre>
                    </div>
                </div>
            </div>
            
            <!-- 错误分析标签页 -->
            <div id="errors" class="tab-content">
                <div class="section">
                    <h2>⚠️ 错误类型统计</h2>
                    <div class="chart-container">
                        {error_chart if error_chart else '<p>暂无错误数据</p>'}
                    </div>
                </div>
                <div class="section">
                    <h2>🔍 错误详情分析</h2>
                    <div class="overview-card">
                        <h3>主要问题</h3>
                        <ul>
                            <li><strong>仿真编译失败</strong>：run_simulation 工具调用时出现语法错误</li>
                            <li><strong>错误信息</strong>：temp_testbench.v:1: syntax error</li>
                            <li><strong>影响</strong>：无法完成功能验证，任务流程未完全闭环</li>
                        </ul>
                        <h3>解决方案建议</h3>
                        <ul>
                            <li>检查 run_simulation 工具的语法处理逻辑</li>
                            <li>改进测试台代码生成的质量控制</li>
                            <li>增加错误恢复机制</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- 文件结构标签页 -->
            <div id="files" class="tab-content">
                <div class="section">
                    <h2>📁 实验文件结构</h2>
                    <div class="file-structure">
                        📂 llm_experiments/
                        <div style="margin-left: 20px;">
                            📂 {self.experiment_id}/
                            <div style="margin-left: 20px;">
                                📂 designs/
                                <div style="margin-left: 20px;">
                                    📄 counter_v2.v (279B)
                                    <br>📄 counter_optimized_v2.v (474B)
                                </div>
                                📂 testbenches/
                                <div style="margin-left: 20px;">
                                    📄 testbench_counter.v (5.3KB)
                                </div>
                                📂 reports/
                                <div style="margin-left: 20px;">
                                    📄 experiment_report.json (26KB)
                                    <br>📄 experiment_summary.txt (476B)
                                </div>
                                📂 artifacts/
                                <div style="margin-left: 20px;">
                                    📄 (仿真相关文件)
                                </div>
                                📂 logs/
                                <div style="margin-left: 20px;">
                                    📄 (日志文件)
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {{
            // 隐藏所有标签页内容
            var tabContents = document.getElementsByClassName('tab-content');
            for (var i = 0; i < tabContents.length; i++) {{
                tabContents[i].classList.remove('active');
            }}
            
            // 移除所有标签的active类
            var navTabs = document.getElementsByClassName('nav-tab');
            for (var i = 0; i < navTabs.length; i++) {{
                navTabs[i].classList.remove('active');
            }}
            
            // 显示选中的标签页
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
        """
        
        # 保存HTML文件
        output_path = f"experiment_visualization_{self.experiment_id}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML报告已生成: {output_path}")
        return output_path

def main():
    """主函数"""
    print("🎯 开始生成V-Agent实验可视化HTML报告...")
    
    visualizer = HTMLVisualizer()
    output_file = visualizer.generate_html_report()
    
    if output_file:
        print(f"\n🎉 报告生成成功！")
        print(f"📄 文件路径: {output_file}")
        print(f"🌐 请在浏览器中打开该文件查看完整报告")
        print(f"\n💡 提示:")
        print(f"   - 双击HTML文件即可在浏览器中打开")
        print(f"   - 报告包含交互式图表，可以缩放、悬停查看详情")
        print(f"   - 使用标签页切换不同的分析视图")
        print(f"   - 新增了对话内容展示功能")
    else:
        print("❌ 报告生成失败，请检查实验数据文件")

if __name__ == "__main__":
    main() 