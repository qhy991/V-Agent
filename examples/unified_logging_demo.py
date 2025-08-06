#!/usr/bin/env python3
"""
🎯 统一日志系统使用示例
==================================================

演示如何使用统一日志系统记录agent的工具调用和对话，
以及如何使用Gradio可视化界面查看执行过程。
"""

import asyncio
import time
from pathlib import Path

# 导入统一日志系统
from core.unified_logging_system import UnifiedLoggingSystem, set_global_logging_system
from gradio_agent_visualizer import GradioAgentVisualizer


async def demo_unified_logging():
    """演示统一日志系统的使用"""
    
    print("🎯 开始统一日志系统演示...")
    
    # 创建统一日志系统实例
    session_id = f"demo_session_{int(time.time())}"
    logging_system = UnifiedLoggingSystem(session_id)
    
    # 设置为全局日志系统
    set_global_logging_system(logging_system)
    
    # 开始任务
    task_id = logging_system.start_task("demo_task", "演示统一日志系统的使用")
    
    # 模拟agent开始工作
    logging_system.log_agent_start("llm_coordinator_agent", "开始协调任务")
    
    # 模拟工具调用
    logging_system.log_tool_call("llm_coordinator_agent", "identify_task_type", 
                                {"user_request": "设计一个8位计数器"})
    
    # 模拟LLM调用
    logging_system.log_llm_call("llm_coordinator_agent", "claude-3.5-sonnet", 
                               prompt_length=150, response_length=300, duration=2.5)
    
    # 模拟工具执行结果
    logging_system.log_tool_result("llm_coordinator_agent", "identify_task_type", 
                                  success=True, result={"task_type": "design"}, duration=1.2)
    
    # 模拟agent切换
    logging_system.log_agent_start("enhanced_real_verilog_agent", "开始Verilog设计")
    
    # 模拟文件操作
    logging_system.log_file_operation("enhanced_real_verilog_agent", "write", 
                                     "counter_8bit.v", file_size=1024, duration=0.5)
    
    # 模拟代码审查
    logging_system.log_agent_start("enhanced_real_code_review_agent", "开始代码审查")
    logging_system.log_tool_call("enhanced_real_code_review_agent", "analyze_code_quality", 
                                {"file_path": "counter_8bit.v"})
    logging_system.log_tool_result("enhanced_real_code_review_agent", "analyze_code_quality", 
                                  success=True, result={"quality_score": 85}, duration=1.8)
    
    # 模拟错误和警告
    logging_system.log_warning("enhanced_real_code_review_agent", "代码风格需要改进", 
                              {"suggestion": "添加更多注释"})
    
    # 结束agent工作
    logging_system.log_agent_end("enhanced_real_verilog_agent", "Verilog设计完成")
    logging_system.log_agent_end("enhanced_real_code_review_agent", "代码审查完成")
    logging_system.log_agent_end("llm_coordinator_agent", "任务协调完成")
    
    # 结束任务
    logging_system.end_task(True, "成功完成8位计数器设计")
    
    print("✅ 统一日志系统演示完成")
    
    return logging_system


def demo_gradio_visualization():
    """演示Gradio可视化界面"""
    
    print("🎨 启动Gradio可视化界面...")
    
    # 创建可视化界面
    visualizer = GradioAgentVisualizer()
    interface = visualizer.create_interface()
    
    # 启动Gradio界面
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=True
    )


async def demo_with_real_agents():
    """使用真实agent演示统一日志系统"""
    
    print("🤖 使用真实agent演示统一日志系统...")
    
    # 创建统一日志系统
    session_id = f"real_demo_{int(time.time())}"
    logging_system = UnifiedLoggingSystem(session_id)
    set_global_logging_system(logging_system)
    
    # 开始任务
    task_id = logging_system.start_task("real_task", "使用真实agent设计Verilog模块")
    
    try:
        # 导入必要的模块
        from core.llm_coordinator_agent import LLMCoordinatorAgent
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewer
        from config.config import FrameworkConfig
        
        # 初始化配置
        config = FrameworkConfig()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        logging_system.log_agent_start("llm_coordinator_agent", "初始化协调智能体")
        
        # 创建Verilog设计智能体
        verilog_agent = EnhancedRealVerilogAgent()
        logging_system.log_agent_start("enhanced_real_verilog_agent", "初始化Verilog设计智能体")
        
        # 创建代码审查智能体
        review_agent = EnhancedRealCodeReviewer()
        logging_system.log_agent_start("enhanced_real_code_review_agent", "初始化代码审查智能体")
        
        # 注册智能体
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(review_agent)
        
        # 执行任务
        result = await coordinator.coordinate_task(
            user_request="设计一个4位加法器模块",
            max_iterations=5
        )
        
        print(f"✅ 任务执行完成: {result.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 任务执行失败: {e}")
        logging_system.log_error("system", "任务执行失败", {"error": str(e)})
    
    finally:
        # 结束任务
        logging_system.end_task(True, "真实agent演示完成")
    
    return logging_system


def main():
    """主函数"""
    
    print("🎯 统一日志系统演示程序")
    print("=" * 50)
    
    # 运行基础演示
    print("\n1. 运行基础演示...")
    logging_system = asyncio.run(demo_unified_logging())
    
    # 显示统计信息
    print("\n📊 执行统计:")
    timeline = logging_system.get_execution_timeline()
    print(f"   - 总事件数: {len(timeline)}")
    
    agent_summary = logging_system.get_agent_performance_summary()
    print(f"   - 参与智能体: {list(agent_summary.keys())}")
    
    tool_summary = logging_system.get_tool_usage_summary()
    print(f"   - 工具调用次数: {sum(tool_summary.values())}")
    
    # 导出数据
    export_path = Path("exports") / f"demo_log_{int(time.time())}.json"
    export_path.parent.mkdir(exist_ok=True)
    logging_system.export_data(str(export_path))
    print(f"   - 数据已导出到: {export_path}")
    
    # 询问是否启动Gradio界面
    print("\n2. 启动Gradio可视化界面...")
    try:
        demo_gradio_visualization()
    except KeyboardInterrupt:
        print("👋 用户中断，程序退出")
    except Exception as e:
        print(f"❌ Gradio启动失败: {e}")
    
    # 询问是否运行真实agent演示
    print("\n3. 运行真实agent演示...")
    try:
        real_logging_system = asyncio.run(demo_with_real_agents())
        print("✅ 真实agent演示完成")
    except Exception as e:
        print(f"❌ 真实agent演示失败: {e}")


if __name__ == "__main__":
    main() 