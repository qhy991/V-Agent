#!/usr/bin/env python3
"""
测试报告修复脚本
================

验证修复后的实验报告系统是否能正确保存所有数据。
"""

import asyncio
import json
import time
from pathlib import Path

from core.llm_coordinator_agent import LLMCoordinatorAgent, TaskContext
from config.config import FrameworkConfig
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent


async def test_report_fix():
    """测试报告修复"""
    print("🧪 开始测试报告修复...")

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

    # 创建模拟的TaskContext
    task_context = TaskContext(
        task_id="test_task_001",
        original_request="设计一个简单的2位计数器"
    )

    # 模拟数据收集
    print("📊 模拟数据收集...")
    
    # 添加工具执行记录
    task_context.add_tool_execution(
        tool_name="identify_task_type",
        parameters={"user_request": "设计计数器"},
        agent_id="llm_coordinator_agent",
        success=True,
        result="任务类型: design",
        execution_time=2.5
    )
    
    task_context.add_tool_execution(
        tool_name="assign_task_to_agent",
        parameters={"agent_id": "enhanced_real_verilog_agent"},
        agent_id="llm_coordinator_agent",
        success=True,
        result="任务分配成功",
        execution_time=1.8
    )

    # 添加文件操作记录
    task_context.add_file_operation(
        operation_type="create",
        file_path="/test/counter.v",
        agent_id="enhanced_real_verilog_agent",
        success=True,
        file_size=1024
    )

    # 添加工作流阶段记录
    task_context.add_workflow_stage(
        stage_name="task_analysis",
        description="分析任务需求",
        agent_id="llm_coordinator_agent",
        duration=3.2,
        success=True
    )

    # 添加LLM对话记录
    task_context.add_llm_conversation(
        agent_id="llm_coordinator_agent",
        conversation_id="test_conv_001",
        system_prompt="你是一个智能协调者...",
        user_message="请设计一个2位计数器",
        assistant_response="我将分析这个任务并分配给合适的智能体...",
        model_name="claude-3.5-sonnet",
        duration=2.5,
        success=True,
        is_first_call=True,
        total_tokens=150
    )

    # 测试数据收集摘要
    print("📋 测试数据收集摘要...")
    summary = task_context.get_data_collection_summary()
    
    print(f"工具调用: {summary['tool_executions']['total']} 次")
    print(f"文件操作: {summary['file_operations']['total']} 次")
    print(f"工作流阶段: {summary['workflow_stages']['total']} 个")
    print(f"LLM对话: {summary['llm_conversations']['total']} 次")

    # 测试最终结果收集
    print("🔍 测试最终结果收集...")
    final_result = coordinator._collect_final_result(
        task_context=task_context,
        coordination_result="任务完成"
    )

    # 检查结果结构
    print("\n📊 检查结果结构...")
    
    # 基本字段检查
    assert "success" in final_result, "缺少success字段"
    assert "task_context" in final_result, "缺少task_context字段"
    
    # TaskContext字段检查
    task_context_data = final_result.get("task_context", {})
    
    # 检查数据收集字段
    data_fields = [
        "tool_executions", "agent_interactions", "performance_metrics",
        "workflow_stages", "file_operations", "execution_timeline",
        "llm_conversations", "data_collection_summary"
    ]
    
    for field in data_fields:
        assert field in task_context_data, f"缺少{field}字段"
        print(f"  ✅ {field}: {len(task_context_data[field]) if isinstance(task_context_data[field], list) else type(task_context_data[field])}")

    # 保存测试结果
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    result_file = output_dir / "report_fix_test_result.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2, default=str)

    print(f"✅ 测试结果已保存到: {result_file}")

    # 显示摘要统计
    print("\n📈 最终统计:")
    print(f"  工具调用: {len(task_context_data.get('tool_executions', []))} 次")
    print(f"  文件操作: {len(task_context_data.get('file_operations', []))} 次")
    print(f"  工作流阶段: {len(task_context_data.get('workflow_stages', []))} 个")
    print(f"  LLM对话: {len(task_context_data.get('llm_conversations', []))} 次")
    print(f"  执行事件: {len(task_context_data.get('execution_timeline', []))} 个")

    return final_result


async def main():
    """主函数"""
    try:
        result = await test_report_fix()
        if result:
            print("\n🎉 报告修复验证成功！")
            print("✅ 所有数据收集字段正常")
            print("✅ 没有出现字段缺失错误")
            print("✅ 实验报告结构完整")
        else:
            print("\n💥 报告修复验证失败！")
    except Exception as e:
        print(f"❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 