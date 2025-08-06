#!/usr/bin/env python3
"""
数据收集功能测试脚本
====================

测试改进后的实验报告系统，验证数据收集功能是否正常工作。
"""

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

from core.llm_coordinator_agent import LLMCoordinatorAgent, TaskContext
from config.config import FrameworkConfig
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent


async def test_data_collection():
    """测试数据收集功能"""
    print("🧪 开始测试数据收集功能...")
    
    # 创建配置
    config = FrameworkConfig()
    config.enable_detailed_logging = True
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent(config)
    
    # 注册智能体
    verilog_agent = EnhancedRealVerilogAgent()
    reviewer_agent = EnhancedRealCodeReviewAgent()
    
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(reviewer_agent)
    
    # 创建任务上下文
    task_context = TaskContext(
        task_id="test_task_001",
        original_request="设计一个简单的4位计数器",
        experiment_path="/tmp/test_experiment"
    )
    
    # 设置任务上下文
    coordinator.current_task_context = task_context
    
    # 模拟工具调用
    print("🔧 模拟工具调用...")
    task_context.add_tool_execution(
        tool_name="identify_task_type",
        parameters={"user_request": "设计一个4位计数器"},
        agent_id="llm_coordinator_agent",
        success=True,
        result={"task_type": "design", "complexity": "medium"},
        execution_time=2.5
    )
    
    task_context.add_tool_execution(
        tool_name="recommend_agent",
        parameters={"task_type": "design", "complexity": "medium"},
        agent_id="llm_coordinator_agent",
        success=True,
        result={"recommended_agent": "enhanced_real_verilog_agent"},
        execution_time=1.8
    )
    
    # 模拟文件操作
    print("📁 模拟文件操作...")
    task_context.add_file_operation(
        operation_type="create",
        file_path="/tmp/test_experiment/designs/counter.v",
        agent_id="enhanced_real_verilog_agent",
        success=True,
        file_size=1024
    )
    
    task_context.add_file_operation(
        operation_type="create",
        file_path="/tmp/test_experiment/testbenches/counter_tb.v",
        agent_id="enhanced_real_code_reviewer",
        success=True,
        file_size=2048
    )
    
    # 模拟工作流阶段
    print("🔄 模拟工作流阶段...")
    task_context.add_workflow_stage(
        stage_name="task_analysis",
        description="分析任务需求",
        agent_id="llm_coordinator_agent",
        duration=3.2,
        success=True
    )
    
    task_context.add_workflow_stage(
        stage_name="agent_execution_enhanced_real_verilog_agent",
        description="Verilog设计智能体执行任务",
        agent_id="enhanced_real_verilog_agent",
        duration=45.6,
        success=True,
        metadata={"task_type": "design", "priority": "medium"}
    )
    
    # 模拟智能体交互
    print("🤖 模拟智能体交互...")
    task_context.agent_interactions.append({
        "timestamp": time.time(),
        "coordinator_id": "llm_coordinator_agent",
        "target_agent_id": "enhanced_real_verilog_agent",
        "task_description": "设计一个4位计数器模块...",
        "success": True,
        "execution_time": 45.6,
        "response_length": 1500
    })
    
    # 🆕 模拟LLM对话记录
    print("🧠 模拟LLM对话记录...")
    task_context.add_llm_conversation(
        agent_id="llm_coordinator_agent",
        conversation_id="coordinator_agent_test_task_001",
        system_prompt="你是一个智能协调者，负责分析任务并分配给合适的智能体...",
        user_message="请设计一个4位计数器模块，包含时钟、复位、使能输入，支持向上计数功能。",
        assistant_response="我将分析这个任务并分配给合适的智能体。这是一个Verilog设计任务，复杂度为中等，建议分配给enhanced_real_verilog_agent。",
        model_name="claude-3.5-sonnet",
        duration=2.5,
        success=True,
        is_first_call=True,
        temperature=0.3,
        max_tokens=4000,
        prompt_tokens=150,
        completion_tokens=80,
        total_tokens=230
    )
    
    task_context.add_llm_conversation(
        agent_id="enhanced_real_verilog_agent",
        conversation_id="verilog_agent_test_task_001",
        system_prompt="你是一个专业的Verilog设计智能体，负责生成高质量的Verilog代码...",
        user_message="设计一个4位计数器模块，包含时钟、复位、使能输入，支持向上计数功能。",
        assistant_response="我将为您设计一个4位计数器模块。这个模块将包含时钟(clk)、复位(rst)、使能(en)输入，以及4位计数输出(count)。",
        model_name="claude-3.5-sonnet",
        duration=3.8,
        success=True,
        is_first_call=True,
        temperature=0.2,
        max_tokens=4000,
        prompt_tokens=200,
        completion_tokens=120,
        total_tokens=320
    )
    
    # 获取数据收集摘要
    print("📊 获取数据收集摘要...")
    summary = task_context.get_data_collection_summary()
    
    # 打印摘要
    print("\n" + "="*60)
    print("📊 数据收集摘要")
    print("="*60)
    
    print(f"工具调用统计:")
    print(f"  总数: {summary['tool_executions']['total']}")
    print(f"  成功: {summary['tool_executions']['successful']}")
    print(f"  失败: {summary['tool_executions']['failed']}")
    print(f"  使用工具: {', '.join(summary['tool_executions']['unique_tools'])}")
    print(f"  总执行时间: {summary['tool_executions']['total_execution_time']:.2f}秒")
    
    print(f"\n文件操作统计:")
    print(f"  总数: {summary['file_operations']['total']}")
    print(f"  成功: {summary['file_operations']['successful']}")
    print(f"  失败: {summary['file_operations']['failed']}")
    print(f"  操作类型: {', '.join(summary['file_operations']['operation_types'])}")
    print(f"  总文件大小: {summary['file_operations']['total_file_size']} 字节")
    
    print(f"\n工作流阶段统计:")
    print(f"  总数: {summary['workflow_stages']['total']}")
    print(f"  成功: {summary['workflow_stages']['successful']}")
    print(f"  失败: {summary['workflow_stages']['failed']}")
    print(f"  总时间: {summary['workflow_stages']['total_duration']:.2f}秒")
    
    print(f"\n智能体交互统计:")
    print(f"  总数: {summary['agent_interactions']['total']}")
    print(f"  成功: {summary['agent_interactions']['successful']}")
    print(f"  失败: {summary['agent_interactions']['failed']}")
    print(f"  参与智能体: {', '.join(summary['agent_interactions']['unique_agents'])}")
    
    print(f"\n执行时间线统计:")
    print(f"  总事件: {summary['execution_timeline']['total_events']}")
    print(f"  事件类型: {', '.join(summary['execution_timeline']['event_types'])}")
    
    print(f"\nLLM对话统计:")
    print(f"  总数: {summary['llm_conversations']['total']}")
    print(f"  成功: {summary['llm_conversations']['successful']}")
    print(f"  失败: {summary['llm_conversations']['failed']}")
    print(f"  参与智能体: {', '.join(summary['llm_conversations']['unique_agents'])}")
    print(f"  使用模型: {', '.join(summary['llm_conversations']['unique_models'])}")
    print(f"  首次调用: {summary['llm_conversations']['first_calls']} 次")
    print(f"  总对话时间: {summary['llm_conversations']['total_duration']:.2f}秒")
    print(f"  总Token数: {summary['llm_conversations']['total_tokens']} 个")
    
    # 测试最终结果收集
    print("\n🔍 测试最终结果收集...")
    final_result = coordinator._collect_final_result(task_context, "任务完成")
    
    # 保存测试结果
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    result_file = output_dir / "data_collection_test_result.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ 测试结果已保存到: {result_file}")
    
    # 验证数据完整性
    print("\n🔍 验证数据完整性...")
    task_context_data = final_result.get('task_context', {})
    
    assert len(task_context_data.get('tool_executions', [])) > 0, "工具调用记录为空"
    assert len(task_context_data.get('file_operations', [])) > 0, "文件操作记录为空"
    assert len(task_context_data.get('workflow_stages', [])) > 0, "工作流阶段记录为空"
    assert len(task_context_data.get('agent_interactions', [])) > 0, "智能体交互记录为空"
    assert len(task_context_data.get('execution_timeline', [])) > 0, "执行时间线记录为空"
    assert len(task_context_data.get('llm_conversations', [])) > 0, "LLM对话记录为空"
    assert task_context_data.get('data_collection_summary'), "数据收集摘要为空"
    
    print("✅ 所有数据收集功能验证通过！")
    
    return final_result


async def main():
    """主函数"""
    try:
        result = await test_data_collection()
        print("\n🎉 数据收集功能测试完成！")
        
        # 显示最终结果摘要
        task_context = result.get('task_context', {})
        summary = task_context.get('data_collection_summary', {})
        
        print(f"\n📈 最终统计:")
        print(f"  工具调用: {summary.get('tool_executions', {}).get('total', 0)} 次")
        print(f"  文件操作: {summary.get('file_operations', {}).get('total', 0)} 次")
        print(f"  工作流阶段: {summary.get('workflow_stages', {}).get('total', 0)} 个")
        print(f"  智能体交互: {summary.get('agent_interactions', {}).get('total', 0)} 次")
        print(f"  执行事件: {summary.get('execution_timeline', {}).get('total_events', 0)} 个")
        print(f"  LLM对话: {summary.get('llm_conversations', {}).get('total', 0)} 次")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 