#!/usr/bin/env python3
"""
实验修复验证测试脚本
====================

验证修复后的实验系统是否能正常运行并生成完整的实验报告。
"""

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

from core.llm_coordinator_agent import LLMCoordinatorAgent
from config.config import FrameworkConfig
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent


async def test_experiment_fix():
    """测试实验修复"""
    print("🧪 开始测试实验修复...")

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

    # 简单的测试任务
    test_request = "设计一个简单的2位计数器模块，包含时钟和复位输入。"

    print(f"📋 测试任务: {test_request}")

    try:
        # 执行协调任务
        result = await coordinator.coordinate_task(
            user_request=test_request,
            conversation_id=f"test_fix_{int(time.time())}",
            max_iterations=3
        )

        print("✅ 任务执行完成")

        # 检查结果结构
        print("\n📊 检查结果结构...")
        
        # 基本字段检查
        assert "success" in result, "缺少success字段"
        assert "task_id" in result, "缺少task_id字段"
        assert "task_context" in result, "缺少task_context字段"
        
        # TaskContext字段检查
        task_context = result.get("task_context", {})
        
        # 检查数据收集字段
        data_fields = [
            "tool_executions", "agent_interactions", "performance_metrics",
            "workflow_stages", "file_operations", "execution_timeline",
            "llm_conversations", "data_collection_summary"
        ]
        
        for field in data_fields:
            assert field in task_context, f"缺少{field}字段"
            print(f"  ✅ {field}: {type(task_context[field])}")

        # 检查数据收集摘要
        summary = task_context.get("data_collection_summary", {})
        summary_fields = [
            "tool_executions", "file_operations", "workflow_stages",
            "agent_interactions", "execution_timeline", "llm_conversations"
        ]
        
        for field in summary_fields:
            assert field in summary, f"缺少{field}摘要"
            print(f"  ✅ {field}摘要: {type(summary[field])}")

        # 保存测试结果
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)

        result_file = output_dir / "experiment_fix_test_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)

        print(f"✅ 测试结果已保存到: {result_file}")

        # 显示摘要统计
        print("\n📈 实验摘要统计:")
        print(f"  任务ID: {result.get('task_id', 'N/A')}")
        print(f"  成功状态: {result.get('success', False)}")
        print(f"  工具调用: {len(task_context.get('tool_executions', []))} 次")
        print(f"  文件操作: {len(task_context.get('file_operations', []))} 次")
        print(f"  工作流阶段: {len(task_context.get('workflow_stages', []))} 个")
        print(f"  LLM对话: {len(task_context.get('llm_conversations', []))} 次")
        print(f"  执行事件: {len(task_context.get('execution_timeline', []))} 个")

        return result

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """主函数"""
    try:
        result = await test_experiment_fix()
        if result:
            print("\n🎉 实验修复验证成功！")
            print("✅ 所有数据收集字段正常")
            print("✅ 没有出现类型错误")
            print("✅ 实验报告结构完整")
        else:
            print("\n💥 实验修复验证失败！")
    except Exception as e:
        print(f"❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 