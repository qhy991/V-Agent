#!/usr/bin/env python3
"""
实验可视化器 - 基于实验报告和日志文件
Experiment Visualizer - Based on experiment reports and log files
"""

import gradio as gr
import json
import os
import re
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

class ExperimentVisualizer:
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
                
            return True
        except Exception as e:
            print(f"加载实验数据失败: {e}")
            return False
    
    def create_experiment_overview(self):
        """创建实验概览"""
        if not hasattr(self, 'experiment_report'):
            return "无法加载实验数据"
        
        report = self.experiment_report
        
        overview_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;">
            <h2 style="margin: 0 0 15px 0;">🎯 实验概览</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <h3 style="margin: 0 0 10px 0;">📊 基本信息</h3>
                    <p><strong>实验ID:</strong> {report.get('experiment_id', 'N/A')}</p>
                    <p><strong>设计类型:</strong> {report.get('design_type', 'N/A')}</p>
                    <p><strong>配置档案:</strong> {report.get('config_profile', 'N/A')}</p>
                    <p><strong>执行状态:</strong> {'✅ 成功' if report.get('success') else '❌ 失败'}</p>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <h3 style="margin: 0 0 10px 0;">⏱️ 性能指标</h3>
                    <p><strong>任务耗时:</strong> {report.get('task_duration', 0):.2f} 秒</p>
                    <p><strong>智能体交互:</strong> {report.get('agent_interaction_count', 0)} 次</p>
                    <p><strong>工作流阶段:</strong> {report.get('workflow_stage_count', 0)} 个</p>
                    <p><strong>工具执行:</strong> {report.get('tool_execution_count', 0)} 次</p>
                </div>
            </div>
        </div>
        """
        return overview_html
    
    def create_workflow_timeline(self):
        """创建工作流时间线"""
        if not hasattr(self, 'experiment_report'):
            return "无法加载实验数据"
        
        timeline_data = self.experiment_report.get('execution_timeline', [])
        
        if not timeline_data:
            return "暂无时间线数据"
        
        # 创建时间线图表
        fig = go.Figure()
        
        for i, event in enumerate(timeline_data):
            timestamp = event.get('timestamp', 0)
            event_type = event.get('event_type', 'unknown')
            agent_id = event.get('agent_id', 'unknown')
            description = event.get('description', '')
            details = event.get('details', {})
            
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
        
        return fig
    
    def create_agent_performance_chart(self):
        """创建智能体性能图表"""
        if not hasattr(self, 'experiment_report'):
            return "无法加载实验数据"
        
        agent_interactions = self.experiment_report.get('agent_interactions', [])
        
        if not agent_interactions:
            return "暂无智能体交互数据"
        
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
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=agents,
            y=execution_times,
            name='执行时间 (秒)',
            marker_color='#2196F3',
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=agents,
            y=response_lengths,
            name='响应长度 (字符)',
            marker_color='#FF9800',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="🤖 智能体性能对比",
            xaxis_title="智能体",
            yaxis_title="执行时间 (秒)",
            yaxis2=dict(
                title="响应长度 (字符)",
                overlaying='y',
                side='right'
            ),
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_file_structure(self):
        """创建文件结构展示"""
        if not hasattr(self, 'experiment_report'):
            return "无法加载实验数据"
        
        # 构建文件树
        file_tree = f"""
        <div style="font-family: 'Courier New', monospace; background: #f5f5f5; padding: 15px; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0;">📁 实验文件结构</h3>
            <div style="color: #333;">
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
        """
        return file_tree
    
    def create_code_comparison(self):
        """创建代码对比展示"""
        if not hasattr(self, 'design_code') or not hasattr(self, 'testbench_code'):
            return "无法加载代码文件"
        
        return {
            "设计代码": self.design_code,
            "测试台代码": self.testbench_code
        }
    
    def create_error_analysis(self):
        """创建错误分析"""
        if not hasattr(self, 'experiment_report'):
            return "无法加载实验数据"
        
        # 分析日志中的错误信息
        error_analysis = """
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0; color: #856404;">⚠️ 错误分析</h3>
            <div style="color: #856404;">
                <h4>主要问题：</h4>
                <ul>
                    <li><strong>仿真编译失败</strong>：run_simulation 工具调用时出现语法错误</li>
                    <li><strong>错误信息</strong>：temp_testbench.v:1: syntax error</li>
                    <li><strong>影响</strong>：无法完成功能验证，任务流程未完全闭环</li>
                </ul>
                
                <h4>解决方案建议：</h4>
                <ul>
                    <li>检查 run_simulation 工具的语法处理逻辑</li>
                    <li>改进测试台代码生成的质量控制</li>
                    <li>增加错误恢复机制</li>
                </ul>
            </div>
        </div>
        """
        return error_analysis

def create_visualization_interface():
    """创建可视化界面"""
    visualizer = ExperimentVisualizer()
    
    # 加载数据
    if not visualizer.load_experiment_data():
        return gr.Interface(
            fn=lambda: "❌ 无法加载实验数据，请检查文件路径",
            inputs=[],
            outputs=gr.Textbox(),
            title="实验可视化器 - 数据加载失败",
            description="请确保实验文件存在且路径正确"
        )
    
    with gr.Blocks(title="V-Agent 实验可视化器", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🎯 V-Agent 实验可视化器")
        gr.Markdown("基于统一日志系统的实验结果可视化展示")
        
        with gr.Tabs():
            # 实验概览标签页
            with gr.Tab("📊 实验概览"):
                gr.HTML(visualizer.create_experiment_overview())
                gr.HTML(visualizer.create_file_structure())
            
            # 工作流分析标签页
            with gr.Tab("🔄 工作流分析"):
                gr.Plot(visualizer.create_workflow_timeline())
                gr.Plot(visualizer.create_agent_performance_chart())
            
            # 代码展示标签页
            with gr.Tab("💻 代码展示"):
                code_comparison = visualizer.create_code_comparison()
                gr.Code(
                    value=code_comparison["设计代码"],
                    language="verilog",
                    label="Verilog设计代码"
                )
                gr.Code(
                    value=code_comparison["测试台代码"],
                    language="verilog",
                    label="测试台代码"
                )
            
            # 错误分析标签页
            with gr.Tab("⚠️ 错误分析"):
                gr.HTML(visualizer.create_error_analysis())
            
            # 原始数据标签页
            with gr.Tab("📄 原始数据"):
                gr.JSON(value=visualizer.experiment_report, label="实验报告JSON")
                gr.Textbox(value=visualizer.experiment_summary, label="实验摘要", lines=10)
    
    return interface

if __name__ == "__main__":
    # 创建并启动可视化界面
    interface = create_visualization_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    ) 