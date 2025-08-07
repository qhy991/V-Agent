#!/usr/bin/env python3
"""
测试协调智能体修复效果
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent, TaskContext
from config.config import FrameworkConfig

async def test_coordinator_fixes():
    """测试协调智能体修复效果"""
    print("🧪 开始测试协调智能体修复效果...")
    
    # 创建配置
    config = FrameworkConfig.from_env()
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent(config)
    
    # 创建测试任务上下文
    task_context = TaskContext(
        task_id="test_task_001",
        original_request="设计一个counter模块并生成测试台"
    )
    coordinator.active_tasks["test_task_001"] = task_context
    
    # 测试1: 任务完成状态检查
    print("\n🔍 测试1: 任务完成状态检查")
    
    # 模拟只有Verilog智能体完成的情况
    task_context.agent_results = {
        "enhanced_real_verilog_agent": {
            "success": True,
            "generated_files": ["counter.v"],
            "result": "module counter;\nendmodule"
        }
    }
    
    # 测试任务完成检查
    completion_result = await coordinator._tool_check_task_completion(
        "test_task_001",
        task_context.agent_results,
        "设计一个counter模块并生成测试台",
        {"require_testbench": True, "require_verification": True}
    )
    
    print(f"✅ 任务完成检查结果:")
    print(f"   成功: {completion_result['success']}")
    print(f"   完成状态: {completion_result.get('is_completed', False)}")
    print(f"   完成分数: {completion_result.get('completion_score', 0)}")
    print(f"   缺失项: {completion_result.get('missing_requirements', [])}")
    
    # 测试2: 协调继续检查
    print("\n🔍 测试2: 协调继续检查")
    
    should_continue = await coordinator._check_coordination_continuation(task_context)
    print(f"✅ 协调继续检查结果: {should_continue}")
    
    # 测试3: 工作流阶段判断
    print("\n🔍 测试3: 工作流阶段判断")
    
    completed_agents = set(task_context.agent_results.keys())
    workflow_stage = coordinator._determine_workflow_stage(completed_agents)
    print(f"✅ 工作流阶段: {workflow_stage}")
    
    # 测试4: 添加代码审查智能体结果
    print("\n🔍 测试4: 添加代码审查智能体结果")
    
    task_context.agent_results["enhanced_real_code_review_agent"] = {
        "success": True,
        "generated_files": ["counter_tb.v"],
        "result": "testbench counter_tb;\nendmodule"
    }
    
    # 再次测试任务完成检查
    completion_result_2 = await coordinator._tool_check_task_completion(
        "test_task_001",
        task_context.agent_results,
        "设计一个counter模块并生成测试台",
        {"require_testbench": True, "require_verification": True}
    )
    
    print(f"✅ 完整任务完成检查结果:")
    print(f"   成功: {completion_result_2['success']}")
    print(f"   完成状态: {completion_result_2.get('is_completed', False)}")
    print(f"   完成分数: {completion_result_2.get('completion_score', 0)}")
    print(f"   缺失项: {completion_result_2.get('missing_requirements', [])}")
    
    # 测试5: 协调继续检查（完整情况）
    print("\n🔍 测试5: 协调继续检查（完整情况）")
    
    should_continue_2 = await coordinator._check_coordination_continuation(task_context)
    print(f"✅ 协调继续检查结果: {should_continue_2}")
    
    # 测试6: 工作流阶段判断（完整情况）
    print("\n🔍 测试6: 工作流阶段判断（完整情况）")
    
    completed_agents_2 = set(task_context.agent_results.keys())
    workflow_stage_2 = coordinator._determine_workflow_stage(completed_agents_2)
    print(f"✅ 工作流阶段: {workflow_stage_2}")
    
    print("\n✅ 所有测试完成！")

if __name__ == "__main__":
    asyncio.run(test_coordinator_fixes()) 