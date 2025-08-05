#!/usr/bin/env python3
"""
多智能体协作对话可视化工具 - Gradio版本

功能特性:
1. 可视化多智能体对话流程
2. 区分显示 System Prompt, User Prompt, 工具调用
3. 实时/非实时模式切换
4. 支持导出对话记录
5. 智能体状态监控
"""

import gradio as gr
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import sys
import socket
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入框架组件
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig

class MultiAgentVisualizer:
    """多智能体协作可视化器"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        self.coordinator = None
        self.verilog_agent = None
        self.review_agent = None
        self.conversation_history = []
        self.agent_states = {}
        self.current_experiment = None
        
    def initialize_agents(self):
        """初始化所有智能体"""
        try:
            self.coordinator = LLMCoordinatorAgent(self.config)
            self.verilog_agent = EnhancedRealVerilogAgent(self.config)
            self.review_agent = EnhancedRealCodeReviewAgent(self.config)
            
            self.agent_states = {
                "coordinator": {"status": "ready", "last_active": time.time()},
                "verilog_agent": {"status": "ready", "last_active": time.time()},
                "review_agent": {"status": "ready", "last_active": time.time()}
            }
            
            return "✅ 所有智能体初始化成功"
        except Exception as e:
            return f"❌ 智能体初始化失败: {str(e)}"
    
    def format_message_display(self, message: Dict[str, Any]) -> str:
        """格式化消息显示"""
        timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
        agent_id = message.get('agent_id', 'unknown')
        msg_type = message.get('type', 'unknown')
        content = message.get('content', '')
        
        # 根据消息类型设置不同的样式
        if msg_type == 'system_prompt':
            return f"""
<div style="border-left: 4px solid #ff6b6b; padding: 10px; margin: 5px 0; background: #fff5f5;">
    <div style="font-weight: bold; color: #ff6b6b;">🔧 System Prompt - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <pre style="white-space: pre-wrap; font-size: 0.85em; max-height: 200px; overflow-y: auto;">{content[:500]}{'...' if len(content) > 500 else ''}</pre>
</div>
"""
        elif msg_type == 'user_prompt':
            return f"""
<div style="border-left: 4px solid #4ecdc4; padding: 10px; margin: 5px 0; background: #f0fdfc;">
    <div style="font-weight: bold; color: #4ecdc4;">👤 User Prompt - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <div style="font-size: 0.9em;">{content}</div>
</div>
"""
        elif msg_type == 'tool_call':
            tool_info = message.get('tool_info', {})
            tool_name = tool_info.get('tool_name', 'unknown')
            parameters = tool_info.get('parameters', {})
            success = tool_info.get('success', False)
            result = tool_info.get('result', '')
            
            status_color = "#45b7d1" if success else "#ff6b6b"
            status_bg = "#f0f9ff" if success else "#fff5f5"
            status_icon = "✅" if success else "❌"
            
            return f"""
<div style="border-left: 4px solid {status_color}; padding: 10px; margin: 5px 0; background: {status_bg};">
    <div style="font-weight: bold; color: {status_color};">{status_icon} Tool Call - {agent_id}</div>
    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">{timestamp}</div>
    <div style="font-weight: bold; margin-bottom: 5px;">🔧 {tool_name}</div>
    <details style="margin-bottom: 5px;">
        <summary style="cursor: pointer; color: #666;">Parameters</summary>
        <pre style="font-size: 0.8em; background: #f8f9fa; padding: 5px; border-radius: 3px; margin-top: 5px;">{json.dumps(parameters, indent=2, ensure_ascii=False)}</pre>
    </details>
    <div style="font-size: 0.85em; max-height: 150px; overflow-y: auto;">{str(result)[:300]}{'...' if len(str(result)) > 300 else ''}</div>
</div>
"""
        elif msg_type == 'assistant_response':
            return f"""
<div style="border-left: 4px solid #95a5a6; padding: 10px; margin: 5px 0; background: #f8f9fa;">
    <div style="font-weight: bold; color: #95a5a6;">🤖 Assistant Response - {agent_id}</div>
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
    
    def add_message(self, agent_id: str, msg_type: str, content: str, **kwargs):
        """添加消息到对话历史"""
        message = {
            'timestamp': time.time(),
            'agent_id': agent_id,
            'type': msg_type,
            'content': content,
            **kwargs
        }
        self.conversation_history.append(message)
        
        # 更新智能体状态
        if agent_id in self.agent_states:
            self.agent_states[agent_id]['last_active'] = time.time()
            self.agent_states[agent_id]['status'] = 'active'
    
    def get_agent_status_display(self) -> str:
        """获取智能体状态显示"""
        status_html = "<div style='display: flex; gap: 20px; margin: 10px 0;'>"
        
        for agent_id, state in self.agent_states.items():
            last_active = time.time() - state['last_active']
            status = state['status']
            
            if last_active < 5:
                color = "#4ecdc4"  # 活跃
                status_text = "🟢 Active"
            elif last_active < 30:
                color = "#f7dc6f"  # 最近活跃
                status_text = "🟡 Recent"
            else:
                color = "#bdc3c7"  # 空闲
                status_text = "⚪ Idle"
            
            status_html += f"""
<div style="border: 2px solid {color}; padding: 8px; border-radius: 8px; text-align: center;">
    <div style="font-weight: bold; color: {color};">{agent_id.replace('_', ' ').title()}</div>
    <div style="font-size: 0.8em;">{status_text}</div>
</div>
"""
        
        status_html += "</div>"
        return status_html
    
    def simulate_conversation(self, user_request: str, mode: str = "step_by_step") -> tuple:
        """模拟对话执行（同步版本用于Gradio）"""
        if not self.coordinator:
            return "❌ 请先初始化智能体", "", ""
        
        # 清空历史记录
        self.conversation_history = []
        
        try:
            # 1. 用户请求
            self.add_message("user", "user_prompt", user_request)
            
            # 2. 协调器分析任务
            self.add_message("coordinator", "system_prompt", 
                           "分析用户需求，确定需要调用的智能体和任务分解")
            
            # 模拟协调器的任务分析过程
            if "counter" in user_request.lower() or "计数器" in user_request:
                # 3. 分配任务给Verilog智能体
                self.add_message("coordinator", "tool_call", 
                               "分配设计任务给Verilog智能体",
                               tool_info={
                                   "tool_name": "assign_task_to_agent",
                                   "parameters": {
                                       "agent_id": "enhanced_real_verilog_agent",
                                       "task_description": "设计counter模块，生成Verilog代码"
                                   },
                                   "success": True,
                                   "result": "任务已分配给Verilog智能体"
                               })
                
                # 4. Verilog智能体执行
                self.add_message("verilog_agent", "system_prompt", 
                               self.verilog_agent._build_enhanced_system_prompt()[:500] + "...")
                
                self.add_message("verilog_agent", "user_prompt", 
                               "设计一个counter模块\n\n🚨 **重要提醒**: ❌ 绝对禁止调用 `generate_testbench` 工具")
                
                # 模拟Verilog智能体的工具调用
                self.add_message("verilog_agent", "tool_call",
                               "分析设计需求",
                               tool_info={
                                   "tool_name": "analyze_design_requirements",
                                   "parameters": {
                                       "requirements": "设计counter模块",
                                       "design_type": "sequential"
                                   },
                                   "success": True,
                                   "result": "需求分析完成：时序逻辑设计，需要时钟和复位信号"
                               })
                
                self.add_message("verilog_agent", "tool_call",
                               "生成Verilog代码",
                               tool_info={
                                   "tool_name": "generate_verilog_code", 
                                   "parameters": {
                                       "module_name": "counter",
                                       "requirements": "8位计数器，带使能和复位"
                                   },
                                   "success": True,
                                   "result": "Verilog代码生成成功，已保存到counter.v文件"
                               })
                
                # 5. 如果需要验证，分配任务给代码审查智能体
                if "验证" in user_request or "测试" in user_request or "testbench" in user_request:
                    self.add_message("coordinator", "tool_call",
                                   "分配验证任务给代码审查智能体",
                                   tool_info={
                                       "tool_name": "assign_task_to_agent",
                                       "parameters": {
                                           "agent_id": "enhanced_real_code_review_agent",
                                           "task_description": "为counter模块生成测试台并执行仿真验证"
                                       },
                                       "success": True,
                                       "result": "任务已分配给代码审查智能体"
                                   })
                    
                    # 6. 代码审查智能体执行
                    self.add_message("review_agent", "system_prompt",
                                   "专业的Verilog代码审查和测试专家，负责生成测试台和执行仿真")
                    
                    self.add_message("review_agent", "tool_call",
                                   "生成测试台",
                                   tool_info={
                                       "tool_name": "generate_testbench",
                                       "parameters": {
                                           "module_name": "counter",
                                           "module_code": "从counter.v读取的代码"
                                       },
                                       "success": True,
                                       "result": "测试台生成成功，已保存到counter_tb.v文件"
                                   })
                    
                    self.add_message("review_agent", "tool_call",
                                   "执行仿真",
                                   tool_info={
                                       "tool_name": "run_simulation",
                                       "parameters": {
                                           "design_file": "counter.v",
                                           "testbench_file": "counter_tb.v"
                                       },
                                       "success": True,
                                       "result": "仿真执行成功，功能验证通过"
                                   })
            
            # 7. 协调器提供最终答案
            self.add_message("coordinator", "assistant_response",
                           "✅ 任务完成！已成功设计counter模块并完成验证。生成的文件：counter.v, counter_tb.v")
            
            # 生成对话显示
            conversation_display = ""
            for msg in self.conversation_history:
                conversation_display += self.format_message_display(msg)
            
            agent_status = self.get_agent_status_display()
            
            # 生成统计信息
            stats = {
                "总消息数": len(self.conversation_history),
                "System Prompt": len([m for m in self.conversation_history if m['type'] == 'system_prompt']),
                "User Prompt": len([m for m in self.conversation_history if m['type'] == 'user_prompt']),
                "工具调用": len([m for m in self.conversation_history if m['type'] == 'tool_call']),
                "Assistant Response": len([m for m in self.conversation_history if m['type'] == 'assistant_response'])
            }
            
            stats_display = f"""
<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
    <h4>📊 对话统计</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
        {' '.join([f'<div style="text-align: center; padding: 8px; background: white; border-radius: 4px;"><strong>{k}</strong><br>{v}</div>' for k, v in stats.items()])}
    </div>
</div>
"""
            
            return conversation_display, agent_status, stats_display
            
        except Exception as e:
            error_msg = f"❌ 对话执行出错: {str(e)}"
            self.add_message("system", "error", error_msg)
            return self.format_message_display(self.conversation_history[-1]), "", ""
    
    def load_experiment_conversation(self, experiment_path: str) -> str:
        """从实验报告加载真实的对话历史"""
        try:
            # 🔧 修复路径拼接问题
            experiment_path = experiment_path.strip()
            if experiment_path.endswith('/reports/experiment_report.json'):
                # 如果用户已经输入了完整路径，直接使用
                report_path = Path(experiment_path)
            else:
                # 标准路径拼接
                report_path = Path(experiment_path) / "reports" / "experiment_report.json"
            
            if not report_path.exists():
                return f"❌ 实验报告文件不存在: {report_path}\n💡 请确认路径格式正确，例如: /path/to/llm_experiments/llm_coordinator_counter_1754356089"
            
            with open(report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 🔧 尝试多种路径提取对话历史
            conversation_history = []
            found_path = None
            
            # 路径 1: detailed_result.conversation_history (标准路径)
            if 'detailed_result' in report_data and 'conversation_history' in report_data['detailed_result']:
                conversation_history = report_data['detailed_result']['conversation_history']
                found_path = "detailed_result.conversation_history"
            
            # 路径 2: 直接在根级别的conversation_history
            elif 'conversation_history' in report_data:
                conversation_history = report_data['conversation_history']
                found_path = "root.conversation_history"
            
            # 路径 3: 嵌套在其他字段中
            elif 'experiment_report' in report_data and 'conversation_history' in report_data['experiment_report']:
                conversation_history = report_data['experiment_report']['conversation_history']
                found_path = "experiment_report.conversation_history"
            
            # 检查实验状态
            experiment_success = report_data.get('success', False)
            experiment_id = report_data.get('experiment_id', 'unknown')
            
            if not conversation_history:
                # 提供详细的调试信息
                available_keys = list(report_data.keys())
                detailed_structure = {}
                
                if 'detailed_result' in report_data:
                    detailed_structure['detailed_result'] = list(report_data['detailed_result'].keys())
                
                debug_info = f"""
⚠️ 实验报告中conversation_history为空或不存在

📊 实验信息:
- 实验ID: {experiment_id}
- 实验状态: {'✅ 成功' if experiment_success else '❌ 失败'}
- 报告路径: {report_path}

📝 数据结构分析:
- 根级别字段: {available_keys}
- detailed_result字段: {detailed_structure.get('detailed_result', '不存在')}

💡 可能的原因:
1. 该实验是在对话历史功能实现之前运行的
2. 实验失败，未记录完整对话历史
3. 使用了旧版本的框架

🚀 建议:
- 运行新的实验来获得完整对话历史
- 使用修改后的框架重新执行实验
"""
                return debug_info.strip()
            
            # 转换为可视化格式
            self.conversation_history = []
            for msg in conversation_history:
                self.add_message_from_experiment(msg)
            
            # 更新智能体状态
            agents_involved = list(set(msg.get('agent_id', 'unknown') for msg in conversation_history))
            for agent_id in agents_involved:
                if agent_id not in self.agent_states:
                    self.agent_states[agent_id] = {
                        "status": "completed",
                        "last_active": time.time()
                    }
            
            return f"✅ 成功加载实验对话历史: {len(conversation_history)} 条消息，涉及 {len(agents_involved)} 个智能体"
            
        except Exception as e:
            return f"❌ 加载实验对话历史失败: {str(e)}"
    
    def add_message_from_experiment(self, exp_msg: dict):
        """从实验消息转换为可视化消息格式"""
        role = exp_msg.get('role', 'unknown')
        content = exp_msg.get('content', '')
        agent_id = exp_msg.get('agent_id', 'unknown')
        tool_info = exp_msg.get('tool_info', {})
        timestamp = exp_msg.get('timestamp', time.time())
        
        # 根据角色映射到可视化类型
        if role == 'system':
            msg_type = 'system_prompt'
        elif role == 'user':
            msg_type = 'user_prompt'
        elif role == 'assistant':
            msg_type = 'assistant_response'
        elif role in ['tool_call', 'tool_result']:
            msg_type = 'tool_call'
        else:
            msg_type = role
        
        message = {
            'timestamp': timestamp,
            'agent_id': agent_id,
            'type': msg_type,
            'content': content,
        }
        
        if tool_info:
            message['tool_info'] = tool_info
        
        self.conversation_history.append(message)
    
    def export_conversation(self) -> str:
        """导出对话记录"""
        if not self.conversation_history:
            return "没有对话记录可导出"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_export_{timestamp}.json"
        filepath = project_root / "exports" / filename
        
        # 确保导出目录存在
        filepath.parent.mkdir(exist_ok=True)
        
        export_data = {
            "timestamp": timestamp,
            "conversation_history": self.conversation_history,
            "agent_states": self.agent_states,
            "stats": {
                "total_messages": len(self.conversation_history),
                "message_types": {}
            }
        }
        
        # 统计消息类型
        for msg in self.conversation_history:
            msg_type = msg['type']
            export_data["stats"]["message_types"][msg_type] = export_data["stats"]["message_types"].get(msg_type, 0) + 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return f"✅ 对话记录已导出到: {filepath}"

# 创建可视化器实例
visualizer = MultiAgentVisualizer()

def create_gradio_interface():
    """创建Gradio界面"""
    
    with gr.Blocks(
        title="多智能体协作可视化工具",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .conversation-display {
            max-height: 600px;
            overflow-y: auto;
        }
        """
    ) as demo:
        
        gr.Markdown("""
        # 🤖 多智能体协作对话可视化工具
        
        可视化Verilog设计智能体协作流程，帮助debug和理解工作流程
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # 输入区域
                gr.Markdown("## 📝 输入测试")
                user_input = gr.Textbox(
                    label="用户请求",
                    placeholder="例如：请设计一个8位counter模块并生成测试台验证",
                    lines=3
                )
                
                with gr.Row():
                    init_btn = gr.Button("🔧 初始化智能体", variant="secondary")
                    simulate_btn = gr.Button("🚀 开始模拟", variant="primary")
                    export_btn = gr.Button("💾 导出记录", variant="secondary")
                
                # 🆕 实验加载功能
                gr.Markdown("### 📁 加载实验对话")
                experiment_path = gr.Textbox(
                    label="实验目录路径",
                    placeholder="例如: /path/to/llm_experiments/llm_coordinator_counter_1754400290",
                    lines=1
                )
                load_experiment_btn = gr.Button("📂 加载实验对话", variant="secondary")
                
                # 系统状态
                gr.Markdown("## 📊 系统状态")
                init_status = gr.HTML(value="❌ 智能体未初始化")
                agent_status = gr.HTML(value="")
                
            with gr.Column(scale=3):
                # 对话显示区域
                gr.Markdown("## 💬 对话流程可视化")
                conversation_display = gr.HTML(
                    value="<p style='text-align: center; color: #666; padding: 50px;'>点击'开始模拟'查看对话流程</p>",
                    elem_classes=["conversation-display"]
                )
        
        # 统计信息
        with gr.Row():
            stats_display = gr.HTML(value="")
        
        # 导出结果
        export_result = gr.Textbox(label="导出结果", visible=False)
        
        # 事件处理
        def handle_init():
            result = visualizer.initialize_agents()
            return result, visualizer.get_agent_status_display()
        
        def handle_simulate(user_request):
            if not user_request.strip():
                return "❌ 请输入用户请求", "", ""
            
            conv_display, agent_stat, stats = visualizer.simulate_conversation(user_request)
            return conv_display, agent_stat, stats
        
        def handle_export():
            result = visualizer.export_conversation()
            return gr.update(value=result, visible=True)
        
        def handle_load_experiment(experiment_path_input):
            if not experiment_path_input.strip():
                return "❌ 请输入实验目录路径", "", ""
            
            result = visualizer.load_experiment_conversation(experiment_path_input.strip())
            
            if result.startswith("✅"):
                # 加载成功，显示对话和统计信息
                conv_display = ""
                for msg in visualizer.conversation_history:
                    conv_display += visualizer.format_message_display(msg)
                
                agent_stat = visualizer.get_agent_status_display()
                
                # 生成统计信息
                stats = {
                    "总消息数": len(visualizer.conversation_history),
                    "System Prompt": len([m for m in visualizer.conversation_history if m['type'] == 'system_prompt']),
                    "User Prompt": len([m for m in visualizer.conversation_history if m['type'] == 'user_prompt']),
                    "工具调用": len([m for m in visualizer.conversation_history if m['type'] == 'tool_call']),
                    "Assistant Response": len([m for m in visualizer.conversation_history if m['type'] == 'assistant_response'])
                }
                
                stats_display = f"""
<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
    <h4>📊 实验对话统计</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
        {' '.join([f'<div style="text-align: center; padding: 8px; background: white; border-radius: 4px;"><strong>{k}</strong><br>{v}</div>' for k, v in stats.items()])}
    </div>
    <div style="margin-top: 10px; padding: 8px; background: #e8f5e8; border-radius: 4px;">
        <strong>加载结果:</strong> {result}
    </div>
</div>
"""
                return conv_display, agent_stat, stats_display
            else:
                # 加载失败
                error_display = f"""
<div style="padding: 20px; text-align: center; color: #666;">
    <h3>加载失败</h3>
    <p>{result}</p>
</div>
"""
                return error_display, "", ""
        
        # 绑定事件
        init_btn.click(
            fn=handle_init,
            outputs=[init_status, agent_status]
        )
        
        simulate_btn.click(
            fn=handle_simulate,
            inputs=[user_input],
            outputs=[conversation_display, agent_status, stats_display]
        )
        
        export_btn.click(
            fn=handle_export,
            outputs=[export_result]
        )
        
        load_experiment_btn.click(
            fn=handle_load_experiment,
            inputs=[experiment_path],
            outputs=[conversation_display, agent_status, stats_display]
        )
        
        # 示例请求
        gr.Markdown("""
        ## 📋 使用说明
        
        ### 🚀 模拟对话模式
        - `请设计一个8位counter模块`
        - `设计一个counter模块并生成测试台验证`  
        - `创建一个带使能和复位的计数器`
        - `设计ALU模块，支持加减法运算`
        
        ### 📂 加载实验对话模式
        1. 运行实验生成对话历史（使用 `test_llm_coordinator_enhanced.py`）
        2. 复制实验目录路径（例如：`llm_experiments/llm_coordinator_counter_1754400290`）
        3. 在上方输入框中粘贴路径并点击"加载实验对话"
        4. 查看真实的多智能体协作对话流程和工具调用详情
        
        ### 💡 特性
        - ✅ 实时可视化多智能体对话流程
        - ✅ 区分显示不同类型的消息（系统提示、工具调用、响应等）
        - ✅ 智能体状态监控
        - ✅ 对话统计分析
        - ✅ 支持导出对话记录
        """)
    
    return demo

def find_available_port(start_port=7862, max_attempts=10):
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
    # 创建导出目录
    (project_root / "exports").mkdir(exist_ok=True)
    
    print("🚀 启动多智能体对话可视化工具...")
    
    # 自动寻找可用端口
    available_port = find_available_port()
    if available_port is None:
        print("❌ 无法找到可用端口，请手动指定GRADIO_SERVER_PORT环境变量")
        sys.exit(1)
    
    print(f"🔧 使用端口: {available_port}")
    
    # 启动Gradio界面
    demo = create_gradio_interface()
    
    try:
        demo.launch(
            server_name="127.0.0.1",
            server_port=available_port,
            share=False,
            debug=False,  # 减少调试信息
            show_error=True,
            quiet=True  # 减少输出
        )
    except KeyboardInterrupt:
        print("\n👋 可视化工具已停止")