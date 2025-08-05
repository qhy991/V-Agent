#!/usr/bin/env python3
"""
简化版多智能体协作对话可视化工具

重点功能:
1. 可视化多智能体对话流程
2. 区分显示 System Prompt, User Prompt, 工具调用
3. 模拟真实的工作流程
4. 导出对话记录
"""

import gradio as gr
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class SimpleAgentVisualizer:
    """简化版多智能体协作可视化器"""
    
    def __init__(self):
        self.conversation_history = []
        self.agent_states = {
            "coordinator": {"status": "ready", "last_active": 0},
            "verilog_agent": {"status": "ready", "last_active": 0},  
            "review_agent": {"status": "ready", "last_active": 0}
        }
        
    def format_message_display(self, message: Dict[str, Any]) -> str:
        """格式化消息显示"""
        timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
        agent_id = message.get('agent_id', 'unknown')
        msg_type = message.get('type', 'unknown')
        content = str(message.get('content', ''))
        
        # 根据消息类型设置不同的样式和颜色
        if msg_type == 'system_prompt':
            return f"""
<div style="border-left: 4px solid #ff6b6b; padding: 10px; margin: 5px 0; background: #fff5f5; border-radius: 5px;">
    <div style="font-weight: bold; color: #ff6b6b; display: flex; align-items: center;">
        🔧 System Prompt - {agent_id.replace('_', ' ').title()} 
        <span style="font-size: 0.8em; color: #666; margin-left: auto;">{timestamp}</span>
    </div>
    <div style="margin-top: 8px; font-family: 'Courier New', monospace; font-size: 0.85em; 
                max-height: 200px; overflow-y: auto; background: white; padding: 8px; border-radius: 3px;">
        {content[:1000]}{'...' if len(content) > 1000 else ''}
    </div>
</div>
"""
        elif msg_type == 'user_prompt':
            return f"""
<div style="border-left: 4px solid #4ecdc4; padding: 10px; margin: 5px 0; background: #f0fdfc; border-radius: 5px;">
    <div style="font-weight: bold; color: #4ecdc4; display: flex; align-items: center;">
        👤 User Prompt - {agent_id.replace('_', ' ').title()}
        <span style="font-size: 0.8em; color: #666; margin-left: auto;">{timestamp}</span>
    </div>
    <div style="margin-top: 8px; font-size: 0.9em;">{content}</div>
</div>
"""
        elif msg_type == 'tool_call':
            tool_info = message.get('tool_info', {})
            tool_name = tool_info.get('tool_name', 'unknown')
            parameters = tool_info.get('parameters', {})
            success = tool_info.get('success', False)
            result = str(tool_info.get('result', ''))
            
            status_color = "#45b7d1" if success else "#ff6b6b"
            status_bg = "#f0f9ff" if success else "#fff5f5"
            status_icon = "✅" if success else "❌"
            
            return f"""
<div style="border-left: 4px solid {status_color}; padding: 10px; margin: 5px 0; background: {status_bg}; border-radius: 5px;">
    <div style="font-weight: bold; color: {status_color}; display: flex; align-items: center;">
        {status_icon} Tool Call - {agent_id.replace('_', ' ').title()}
        <span style="font-size: 0.8em; color: #666; margin-left: auto;">{timestamp}</span>
    </div>
    <div style="font-weight: bold; margin: 8px 0 5px 0; color: #333;">🔧 {tool_name}</div>
    <details style="margin-bottom: 8px; cursor: pointer;">
        <summary style="color: #666; font-size: 0.9em;">📋 Parameters</summary>
        <div style="font-family: 'Courier New', monospace; font-size: 0.8em; background: white; 
                    padding: 8px; border-radius: 3px; margin-top: 5px; border: 1px solid #e0e0e0;">
            {json.dumps(parameters, indent=2, ensure_ascii=False)}
        </div>
    </details>
    <div style="font-size: 0.85em; background: white; padding: 8px; border-radius: 3px; 
                max-height: 150px; overflow-y: auto; border: 1px solid #e0e0e0;">
        {result[:500]}{'...' if len(result) > 500 else ''}
    </div>
</div>
"""
        elif msg_type == 'assistant_response':
            return f"""
<div style="border-left: 4px solid #95a5a6; padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px;">
    <div style="font-weight: bold; color: #95a5a6; display: flex; align-items: center;">
        🤖 Assistant Response - {agent_id.replace('_', ' ').title()}
        <span style="font-size: 0.8em; color: #666; margin-left: auto;">{timestamp}</span>
    </div>
    <div style="margin-top: 8px; font-size: 0.9em;">{content}</div>
</div>
"""
        else:
            return f"""
<div style="border-left: 4px solid #bdc3c7; padding: 10px; margin: 5px 0; background: #ecf0f1; border-radius: 5px;">
    <div style="font-weight: bold; color: #7f8c8d; display: flex; align-items: center;">
        📝 {msg_type.title()} - {agent_id.replace('_', ' ').title()}
        <span style="font-size: 0.8em; color: #666; margin-left: auto;">{timestamp}</span>
    </div>
    <div style="margin-top: 8px; font-size: 0.9em;">{content}</div>
</div>
"""
    
    def add_message(self, agent_id: str, msg_type: str, content: str, **kwargs):
        """添加消息到对话记录"""
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
        current_time = time.time()
        
        status_items = []
        for agent_id, state in self.agent_states.items():
            last_active = current_time - state.get('last_active', 0)
            
            if last_active < 5:
                color = "#4ecdc4"
                status_text = "🟢 Active"
                border_style = "2px solid"
            elif last_active < 30:
                color = "#f7dc6f"
                status_text = "🟡 Recent"
                border_style = "2px solid"
            else:
                color = "#bdc3c7"
                status_text = "⚪ Idle"
                border_style = "1px solid"
            
            status_items.append(f"""
<div style="border: {border_style} {color}; padding: 12px; border-radius: 8px; 
            text-align: center; background: white; min-width: 120px;">
    <div style="font-weight: bold; color: {color}; margin-bottom: 4px;">
        {agent_id.replace('_', ' ').title()}
    </div>
    <div style="font-size: 0.8em; color: #666;">{status_text}</div>
</div>
""")
        
        return f"""
<div style="display: flex; gap: 15px; margin: 10px 0; flex-wrap: wrap; justify-content: center;">
    {''.join(status_items)}
</div>
"""
    
    def simulate_conversation(self, user_request: str) -> tuple:
        """模拟完整的多智能体对话流程"""
        if not user_request.strip():
            return "❌ 请输入用户请求", "", ""
        
        # 清空历史记录
        self.conversation_history = []
        
        try:
            # === 第1步: 用户发起请求 ===
            self.add_message("user", "user_prompt", user_request)
            
            # === 第2步: 协调器接收并分析任务 ===
            coordinator_system_prompt = """你是一个AI协调智能体，负责：
1. 分析用户需求
2. 决定调用哪个智能体
3. 分解复合任务
4. 协调多智能体协作

智能体分工：
- enhanced_real_verilog_agent: 负责Verilog设计代码生成
- enhanced_real_code_review_agent: 负责测试台生成和仿真验证
"""
            
            self.add_message("coordinator", "system_prompt", coordinator_system_prompt)
            
            # 协调器分析任务类型
            if any(keyword in user_request.lower() for keyword in ["counter", "计数器", "设计", "模块"]):
                # === 第3步: 协调器分配设计任务给Verilog智能体 ===
                self.add_message("coordinator", "tool_call", 
                               "分析用户需求，分配设计任务给Verilog智能体",
                               tool_info={
                                   "tool_name": "assign_task_to_agent",
                                   "parameters": {
                                       "agent_id": "enhanced_real_verilog_agent",
                                       "task_description": f"根据用户需求设计Verilog模块: {user_request}"
                                   },
                                   "success": True,
                                   "result": "✅ 设计任务已成功分配给Verilog智能体"
                               })
                
                # === 第4步: Verilog智能体接收任务 ===
                verilog_system_prompt = """你是一位资深的Verilog硬件设计专家，专门负责：
- Verilog/SystemVerilog模块设计和代码生成
- 组合逻辑和时序逻辑设计
- 代码质量分析和最佳实践应用

🚨 重要约束:
❌ 绝对禁止调用 generate_testbench 工具
❌ 绝对禁止调用 update_verilog_code 工具  
❌ 绝对禁止调用 run_simulation 工具
✅ 只能调用设计相关工具: analyze_design_requirements, generate_verilog_code, write_file

如果涉及测试台生成，请明确回复："测试台生成由代码审查智能体负责"
"""
                
                self.add_message("verilog_agent", "system_prompt", verilog_system_prompt)
                
                # Verilog智能体收到包含提醒的用户请求
                enhanced_user_request = f"""{user_request}

🚨 **重要提醒 - 每次工具调用都必须遵守**:
❌ 绝对禁止调用 `generate_testbench` 工具
❌ 绝对禁止调用 `update_verilog_code` 工具  
❌ 绝对禁止调用 `run_simulation` 工具
✅ 只能调用已注册的设计工具: analyze_design_requirements, generate_verilog_code, write_file, read_file

现在请严格按照可用工具列表进行工具调用："""
                
                self.add_message("verilog_agent", "user_prompt", enhanced_user_request)
                
                # === 第5步: Verilog智能体执行设计工具调用 ===
                # 5.1: 分析设计需求
                self.add_message("verilog_agent", "tool_call",
                               "分析用户的设计需求",
                               tool_info={
                                   "tool_name": "analyze_design_requirements",
                                   "parameters": {
                                       "requirements": user_request,
                                       "design_type": "sequential" if "counter" in user_request.lower() else "mixed",
                                       "complexity_level": "medium"
                                   },
                                   "success": True,
                                   "result": "✅ 需求分析完成：这是一个时序逻辑设计，需要时钟和复位信号，包含计数功能"
                               })
                
                # 5.2: 生成Verilog代码
                module_name = "counter" if "counter" in user_request.lower() else "design_module"
                self.add_message("verilog_agent", "tool_call",
                               "生成Verilog设计代码",
                               tool_info={
                                   "tool_name": "generate_verilog_code",
                                   "parameters": {
                                       "module_name": module_name,
                                       "requirements": user_request,
                                       "input_ports": [
                                           {"name": "clk", "width": 1, "description": "时钟信号"},
                                           {"name": "rst", "width": 1, "description": "复位信号"},
                                           {"name": "enable", "width": 1, "description": "使能信号"}
                                       ],
                                       "output_ports": [
                                           {"name": "count", "width": 8, "description": "计数输出"}
                                       ]
                                   },
                                   "success": True,
                                   "result": f"✅ Verilog代码生成成功！模块 {module_name} 已保存到 {module_name}.v 文件"
                               })
                
                # 5.3: 保存文件
                self.add_message("verilog_agent", "tool_call",
                               "保存生成的Verilog文件",
                               tool_info={
                                   "tool_name": "write_file",
                                   "parameters": {
                                       "filename": f"{module_name}.v",
                                       "content": f"// Generated {module_name} module\nmodule {module_name}(input clk, rst, enable, output reg [7:0] count);\n// Module implementation here\nendmodule",
                                       "description": f"生成的{module_name}模块Verilog代码"
                                   },
                                   "success": True,
                                   "result": f"✅ 文件保存成功: ./designs/{module_name}.v"
                               })
                
                # === 第6步: 如果需要验证，协调器分配测试任务给代码审查智能体 ===
                if any(keyword in user_request.lower() for keyword in ["验证", "测试", "testbench", "仿真"]):
                    self.add_message("coordinator", "tool_call",
                                   "分配验证任务给代码审查智能体",
                                   tool_info={
                                       "tool_name": "assign_task_to_agent", 
                                       "parameters": {
                                           "agent_id": "enhanced_real_code_review_agent",
                                           "task_description": f"为{module_name}模块生成测试台并执行仿真验证"
                                       },
                                       "success": True,
                                       "result": "✅ 验证任务已成功分配给代码审查智能体"
                                   })
                    
                    # === 第7步: 代码审查智能体执行验证 ===
                    review_system_prompt = """你是专业的Verilog代码审查和测试专家，负责：
- 生成全面的测试台 (testbench)
- 执行仿真验证
- 分析测试结果
- 提供代码质量评估

可用工具: generate_testbench, run_simulation, analyze_code_quality
"""
                    
                    self.add_message("review_agent", "system_prompt", review_system_prompt)
                    
                    self.add_message("review_agent", "user_prompt", 
                                   f"请为{module_name}模块生成测试台并执行仿真验证")
                    
                    # 7.1: 生成测试台
                    self.add_message("review_agent", "tool_call",
                                   "生成测试台文件",
                                   tool_info={
                                       "tool_name": "generate_testbench",
                                       "parameters": {
                                           "module_name": module_name,
                                           "module_code": f"从{module_name}.v读取的代码内容",  
                                           "testbench_name": f"{module_name}_tb"
                                       },
                                       "success": True,
                                       "result": f"✅ 测试台生成成功！已保存到 {module_name}_tb.v 文件"
                                   })
                    
                    # 7.2: 执行仿真
                    self.add_message("review_agent", "tool_call",
                                   "执行仿真验证",
                                   tool_info={
                                       "tool_name": "run_simulation",
                                       "parameters": {
                                           "design_file": f"{module_name}.v",
                                           "testbench_file": f"{module_name}_tb.v",
                                           "simulation_time": "1000ns"
                                       },
                                       "success": True,
                                       "result": "✅ 仿真执行成功！功能验证通过，时序满足要求"
                                   })
                
                # === 第8步: 协调器提供最终结果 ===
                final_result = f"✅ {module_name}模块设计完成！\n"
                final_result += "📁 生成的文件:\n"
                final_result += f"  - {module_name}.v (设计文件)\n"
                if any(keyword in user_request.lower() for keyword in ["验证", "测试", "testbench", "仿真"]):
                    final_result += f"  - {module_name}_tb.v (测试台文件)\n"
                    final_result += "🧪 验证结果: 功能测试通过"
                
                self.add_message("coordinator", "assistant_response", final_result)
            
            else:
                # 处理其他类型的请求
                self.add_message("coordinator", "assistant_response", 
                               "请提供更具体的Verilog设计需求，例如：设计一个8位计数器模块")
            
            # 生成显示内容
            conversation_display = ""
            for msg in self.conversation_history:
                conversation_display += self.format_message_display(msg)
            
            agent_status = self.get_agent_status_display()
            
            # 生成统计信息
            stats = self._generate_stats()
            
            return conversation_display, agent_status, stats
            
        except Exception as e:
            error_msg = f"❌ 对话模拟出错: {str(e)}"
            return f"<div style='color: red; padding: 20px;'>{error_msg}</div>", "", ""
    
    def _generate_stats(self) -> str:
        """生成统计信息"""
        stats = {
            "总消息数": len(self.conversation_history),
            "System Prompt": len([m for m in self.conversation_history if m['type'] == 'system_prompt']),
            "User Prompt": len([m for m in self.conversation_history if m['type'] == 'user_prompt']),
            "工具调用": len([m for m in self.conversation_history if m['type'] == 'tool_call']),
            "Assistant Response": len([m for m in self.conversation_history if m['type'] == 'assistant_response'])
        }
        
        stats_html = """
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
            padding: 20px; border-radius: 10px; margin: 15px 0;">
    <h4 style="color: #2c3e50; margin-bottom: 15px; text-align: center;">📊 对话统计分析</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); 
                gap: 15px; margin-bottom: 15px;">
"""
        
        colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"]
        for i, (key, value) in enumerate(stats.items()):
            color = colors[i % len(colors)]
            stats_html += f"""
        <div style="text-align: center; padding: 15px; background: white; 
                    border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-top: 4px solid {color};">
            <div style="font-size: 1.8em; font-weight: bold; color: {color};">{value}</div>
            <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 5px;">{key}</div>
        </div>
"""
        
        # 添加流程图
        stats_html += """
    </div>
    <div style="background: white; padding: 15px; border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h5 style="color: #2c3e50; margin-bottom: 10px;">🔄 工作流程</h5>
        <div style="display: flex; align-items: center; justify-content: space-between; 
                    font-size: 0.9em; color: #34495e;">
            <span>👤 用户请求</span>
            <span>→</span>
            <span>🧠 协调器分析</span>
            <span>→</span>
            <span>🔧 Verilog设计</span>
            <span>→</span>
            <span>🧪 代码审查</span>
            <span>→</span>
            <span>✅ 完成</span>
        </div>
    </div>
</div>
"""
        
        return stats_html
    
    def export_conversation(self) -> str:
        """导出对话记录"""
        if not self.conversation_history:
            return "❌ 没有对话记录可导出"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_export_{timestamp}.json"
        
        # 确保exports目录存在
        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)
        filepath = exports_dir / filename
        
        export_data = {
            "export_time": timestamp,
            "conversation_history": self.conversation_history,
            "agent_states": self.agent_states,
            "summary": {
                "total_messages": len(self.conversation_history),
                "agents_involved": list(set(msg['agent_id'] for msg in self.conversation_history)),
                "message_types": {}
            }
        }
        
        # 统计消息类型
        for msg in self.conversation_history:
            msg_type = msg['type']
            export_data["summary"]["message_types"][msg_type] = \
                export_data["summary"]["message_types"].get(msg_type, 0) + 1
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            return f"✅ 对话记录已成功导出到: {filepath}\n📊 包含 {len(self.conversation_history)} 条消息"
        except Exception as e:
            return f"❌ 导出失败: {str(e)}"

# 创建全局可视化器实例
visualizer = SimpleAgentVisualizer()

def create_gradio_interface():
    """创建Gradio界面"""
    
    with gr.Blocks(
        title="多智能体协作可视化工具",
        theme=gr.themes.Default(primary_hue="blue", secondary_hue="gray"),
    ) as interface:
        
        gr.HTML("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    color: white; border-radius: 10px; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.5em;">🤖 多智能体协作可视化工具</h1>
            <p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;">
                可视化Verilog设计智能体协作流程，帮助debug和理解工作流程
            </p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📝 测试输入")
                
                user_input = gr.Textbox(
                    label="用户请求",
                    placeholder="例如：请设计一个8位counter模块并生成测试台验证",
                    lines=4,
                    info="输入你想要测试的Verilog设计需求"
                )
                
                with gr.Row():
                    simulate_btn = gr.Button("🚀 开始模拟", variant="primary", size="lg")
                    export_btn = gr.Button("💾 导出记录", variant="secondary")
                
                # 智能体状态显示
                gr.Markdown("## 🔍 智能体状态")
                agent_status = gr.HTML(
                    value=visualizer.get_agent_status_display(),
                    label="Agent Status"
                )
                
                # 示例请求
                gr.Markdown("""
                ## 📋 测试示例
                
                **基础设计:**
                - `请设计一个8位counter模块`
                - `设计一个带使能的计数器`
                
                **设计+验证:**
                - `设计counter模块并生成测试台验证`
                - `创建一个计数器并执行仿真测试`
                
                **其他模块:**
                - `设计一个ALU模块，支持加减法`
                - `创建一个状态机模块`
                """)
                
            with gr.Column(scale=2):
                gr.Markdown("## 💬 对话流程可视化")
                
                conversation_display = gr.HTML(
                    value="""
                    <div style='text-align: center; color: #666; padding: 50px; 
                                background: #f8f9fa; border-radius: 10px; border: 2px dashed #dee2e6;'>
                        <h3>🎬 准备就绪</h3>
                        <p>点击"开始模拟"按钮查看多智能体协作对话流程</p>
                        <div style='margin-top: 20px; font-size: 0.9em;'>
                            💡 提示：对话会显示System Prompt、User Prompt和工具调用的完整过程
                        </div>
                    </div>
                    """,
                    elem_id="conversation-display"
                )
        
        # 统计信息显示区域
        stats_display = gr.HTML(value="")
        
        # 导出结果显示
        export_result = gr.Textbox(
            label="导出结果", 
            visible=False,
            lines=2
        )
        
        # 事件处理函数
        def handle_simulate(request):
            if not request.strip():
                return (
                    "<div style='color: red; text-align: center; padding: 20px;'>❌ 请输入用户请求</div>",
                    visualizer.get_agent_status_display(),
                    ""
                )
            
            conv_display, agent_stat, stats = visualizer.simulate_conversation(request)
            return conv_display, agent_stat, stats
        
        def handle_export():
            result = visualizer.export_conversation()
            return gr.update(value=result, visible=True)
        
        # 绑定事件
        simulate_btn.click(
            fn=handle_simulate,
            inputs=[user_input],
            outputs=[conversation_display, agent_status, stats_display]
        )
        
        export_btn.click(
            fn=handle_export,
            outputs=[export_result]
        )
        
        # 页面底部信息
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #666; border-top: 1px solid #eee; margin-top: 30px;">
            <p>🔧 多智能体协作框架可视化工具 | 帮助理解Verilog设计智能体工作流程</p>
        </div>
        """)
    
    return interface

if __name__ == "__main__":
    # 创建必要的目录
    Path("exports").mkdir(exist_ok=True)
    
    # 启动界面
    demo = create_gradio_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7862,
        share=False,
        debug=True,
        show_error=True,
        quiet=False
    )