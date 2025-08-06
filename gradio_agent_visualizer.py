"""
🎯 Gradio Agent可视化界面
==================================================

基于统一日志系统的Gradio可视化界面，展示：
- 实时执行时间线
- 智能体性能统计
- 工具使用分析
- 文件操作追踪
- 错误和警告信息
"""

import gradio as gr
import json
import time
from typing import Dict, List, Any
from core.unified_logging_system import get_global_logging_system, UnifiedLoggingSystem


class GradioAgentVisualizer:
    """Gradio智能体可视化器"""
    
    def __init__(self):
        self.logging_system = get_global_logging_system()
        
    def create_interface(self):
        """创建Gradio界面"""
        
        with gr.Blocks(title="🎯 Agent执行可视化", theme=gr.themes.Soft()) as interface:
            
            # 标题
            gr.Markdown("# 🎯 Agent执行可视化系统")
            gr.Markdown("实时监控和可视化多智能体系统的执行过程")
            
            with gr.Row():
                # 左侧：实时监控
                with gr.Column(scale=2):
                    gr.Markdown("## 📊 实时执行时间线")
                    
                    # 执行时间线
                    timeline_output = gr.JSON(
                        label="执行时间线",
                        interactive=False,
                        height=400
                    )
                    
                    # 刷新按钮
                    refresh_btn = gr.Button("🔄 刷新数据", variant="primary")
                    
                # 右侧：统计信息
                with gr.Column(scale=1):
                    gr.Markdown("## 📈 性能统计")
                    
                    # 任务信息
                    task_info = gr.JSON(
                        label="任务信息",
                        interactive=False
                    )
                    
                    # 智能体性能
                    agent_performance = gr.JSON(
                        label="智能体性能",
                        interactive=False
                    )
                    
                    # 工具使用统计
                    tool_usage = gr.JSON(
                        label="工具使用统计",
                        interactive=False
                    )
            
            with gr.Row():
                # 文件操作追踪
                with gr.Column(scale=1):
                    gr.Markdown("## 📁 文件操作")
                    file_operations = gr.JSON(
                        label="文件操作记录",
                        interactive=False
                    )
                
                # 错误和警告
                with gr.Column(scale=1):
                    gr.Markdown("## ⚠️ 错误和警告")
                    errors_warnings = gr.JSON(
                        label="错误和警告",
                        interactive=False
                    )
            
            # 详细事件查看
            with gr.Row():
                gr.Markdown("## 🔍 详细事件查看")
                
                # 事件筛选
                with gr.Column(scale=1):
                    category_filter = gr.Dropdown(
                        choices=["全部", "task", "agent", "tool", "llm", "file", "system"],
                        value="全部",
                        label="事件类别"
                    )
                    
                    level_filter = gr.Dropdown(
                        choices=["全部", "debug", "info", "warning", "error"],
                        value="全部",
                        label="日志级别"
                    )
                    
                    agent_filter = gr.Dropdown(
                        choices=["全部"],
                        value="全部",
                        label="智能体"
                    )
                
                # 事件列表
                with gr.Column(scale=2):
                    filtered_events = gr.JSON(
                        label="筛选后的事件",
                        interactive=False,
                        height=300
                    )
            
            # 导出功能
            with gr.Row():
                gr.Markdown("## 💾 数据导出")
                
                export_btn = gr.Button("📥 导出完整数据", variant="secondary")
                export_output = gr.JSON(
                    label="导出数据",
                    interactive=False
                )
            
            # 事件处理
            def refresh_data():
                """刷新所有数据"""
                data = self.logging_system.export_data()
                
                # 更新智能体筛选选项
                agent_choices = ["全部"] + list(data.get("agent_performance", {}).keys())
                
                return (
                    data.get("execution_timeline", []),
                    data.get("task_summary", {}),
                    data.get("agent_performance", {}),
                    data.get("tool_usage", {}),
                    self._get_file_operations(),
                    self._get_errors_warnings(),
                    agent_choices,
                    self._get_filtered_events("全部", "全部", "全部")
                )
            
            def filter_events(category, level, agent):
                """筛选事件"""
                return self._get_filtered_events(category, level, agent)
            
            def export_data():
                """导出完整数据"""
                return self.logging_system.export_data()
            
            # 绑定事件
            refresh_btn.click(
                fn=refresh_data,
                outputs=[
                    timeline_output,
                    task_info,
                    agent_performance,
                    tool_usage,
                    file_operations,
                    errors_warnings,
                    agent_filter,
                    filtered_events
                ]
            )
            
            category_filter.change(
                fn=filter_events,
                inputs=[category_filter, level_filter, agent_filter],
                outputs=[filtered_events]
            )
            
            level_filter.change(
                fn=filter_events,
                inputs=[category_filter, level_filter, agent_filter],
                outputs=[filtered_events]
            )
            
            agent_filter.change(
                fn=filter_events,
                inputs=[category_filter, level_filter, agent_filter],
                outputs=[filtered_events]
            )
            
            export_btn.click(
                fn=export_data,
                outputs=[export_output]
            )
            
            # 初始化数据
            interface.load(
                fn=refresh_data,
                outputs=[
                    timeline_output,
                    task_info,
                    agent_performance,
                    tool_usage,
                    file_operations,
                    errors_warnings,
                    agent_filter,
                    filtered_events
                ]
            )
            
        return interface
    
    def _get_file_operations(self) -> List[Dict[str, Any]]:
        """获取文件操作记录"""
        file_ops = []
        
        for event in self.logging_system.events:
            if event.category.value == "file":
                file_ops.append({
                    "timestamp": event.timestamp,
                    "agent_id": event.agent_id,
                    "operation": event.details.get("operation", ""),
                    "file_path": event.details.get("file_path", ""),
                    "success": event.success,
                    "details": event.details.get("details", "")
                })
        
        return file_ops
    
    def _get_errors_warnings(self) -> List[Dict[str, Any]]:
        """获取错误和警告记录"""
        errors_warnings = []
        
        for event in self.logging_system.events:
            if event.level.value in ["warning", "error"]:
                errors_warnings.append({
                    "timestamp": event.timestamp,
                    "level": event.level.value,
                    "agent_id": event.agent_id,
                    "title": event.title,
                    "message": event.message,
                    "details": event.details
                })
        
        return errors_warnings
    
    def _get_filtered_events(self, category: str, level: str, agent: str) -> List[Dict[str, Any]]:
        """获取筛选后的事件"""
        filtered_events = []
        
        for event in self.logging_system.events:
            # 类别筛选
            if category != "全部" and event.category.value != category:
                continue
            
            # 级别筛选
            if level != "全部" and event.level.value != level:
                continue
            
            # 智能体筛选
            if agent != "全部" and event.agent_id != agent:
                continue
            
            filtered_events.append({
                "timestamp": event.timestamp,
                "event_id": event.event_id,
                "category": event.category.value,
                "level": event.level.value,
                "agent_id": event.agent_id,
                "title": event.title,
                "message": event.message,
                "color": event.color,
                "icon": event.icon,
                "success": event.success,
                "duration": event.duration,
                "details": event.details,
                "priority": event.priority
            })
        
        # 按时间倒序排列
        filtered_events.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return filtered_events


def create_demo_interface():
    """创建演示界面"""
    
    # 创建演示数据
    demo_system = UnifiedLoggingSystem("demo_session")
    
    # 模拟任务执行
    demo_system.start_task("demo_task", "设计一个counter模块")
    
    # 模拟智能体执行
    demo_system.log_agent_start("enhanced_real_verilog_agent", "设计Verilog模块")
    
    # 模拟工具调用
    demo_system.log_tool_call("enhanced_real_verilog_agent", "generate_verilog_code", 
                             {"module_name": "counter"}, time.time() - 10)
    demo_system.log_tool_result("enhanced_real_verilog_agent", "generate_verilog_code", 
                               True, "成功生成counter.v", duration=5.2)
    
    demo_system.log_file_operation("enhanced_real_verilog_agent", "write_file", 
                                  "designs/counter.v", True, "文件写入成功")
    
    demo_system.log_llm_call("enhanced_real_verilog_agent", "claude-3.5-sonnet", 
                            "请设计一个counter模块", "好的，我来设计一个counter模块...", duration=3.1)
    
    demo_system.log_agent_end("enhanced_real_verilog_agent", True, "成功设计counter模块", duration=15.3)
    
    # 模拟代码审查智能体
    demo_system.log_agent_start("enhanced_real_code_review_agent", "审查代码质量")
    
    demo_system.log_tool_call("enhanced_real_code_review_agent", "analyze_code_quality", 
                             {"file_path": "designs/counter.v"}, time.time() - 5)
    demo_system.log_tool_result("enhanced_real_code_review_agent", "analyze_code_quality", 
                               True, "代码质量评分: 85分", duration=2.8)
    
    demo_system.log_agent_end("enhanced_real_code_review_agent", True, "代码审查完成", duration=8.2)
    
    # 模拟错误
    demo_system.log_error("enhanced_real_verilog_agent", "编译失败", "compilation_error", 
                         {"error_code": "E001", "line": 15})
    
    demo_system.log_warning("enhanced_real_code_review_agent", "代码风格需要改进", 
                           {"suggestion": "添加更多注释"})
    
    # 结束任务
    demo_system.end_task(True, "成功完成counter模块设计")
    
    # 设置全局日志系统
    from core.unified_logging_system import set_global_logging_system
    set_global_logging_system(demo_system)
    
    # 创建可视化界面
    visualizer = GradioAgentVisualizer()
    return visualizer.create_interface()


if __name__ == "__main__":
    # 启动演示界面
    demo_interface = create_demo_interface()
    demo_interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=True
    ) 