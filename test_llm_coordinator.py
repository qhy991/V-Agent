#!/usr/bin/env python3
"""
测试LLM协调智能体框架

Test LLM Coordinator Agent Framework
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.enhanced_logging_config import get_test_logger


async def test_llm_coordinator_basic():
    """测试LLM协调智能体基本功能"""
    
    # 设置日志
    logger = get_test_logger()
    logger.info("🚀 开始测试LLM协调智能体基本功能")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        
        # 创建并注册工作智能体（仅限实际存在的两个智能体）
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_reviewer_agent)
        
        # 生成唯一的对话ID
        conversation_id = f"test_llm_coordinator_{int(time.time())}"
        
        # 测试任务
        test_request = """
请设计一个8位加法器模块，包含：
1. 基本的加法功能
2. 进位输出
3. 溢出检测
4. 相应的测试台和仿真验证

请确保代码质量和功能完整性。
"""
        
        logger.info(f"📋 测试请求: {test_request}")
        logger.info(f"🔗 对话ID: {conversation_id}")
        
        # 执行协调任务
        start_time = time.time()
        
        result = await coordinator.coordinate_task(
            user_request=test_request,
            conversation_id=conversation_id,
            max_iterations=15
        )
        
        execution_time = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("🎉 测试完成！")
        logger.info(f"⏱️ 执行时间: {execution_time:.1f}秒")
        logger.info("=" * 80)
        
        # 显示结果摘要
        print("\n" + "=" * 80)
        print("🎯 LLM协调智能体测试结果")
        print("=" * 80)
        print(f"✅ 执行时间: {execution_time:.1f}秒")
        print(f"🔗 对话ID: {conversation_id}")
        print(f"📊 任务ID: {result.get('task_id', 'unknown')}")
        print(f"🎭 协调结果长度: {len(result.get('coordination_result', ''))}字符")
        
        # 显示智能体执行摘要
        execution_summary = result.get('execution_summary', {})
        print(f"\n📈 执行摘要:")
        print(f"   - 总迭代次数: {execution_summary.get('total_iterations', 0)}")
        print(f"   - 分配的智能体: {', '.join(execution_summary.get('assigned_agents', []))}")
        print(f"   - 执行时间: {execution_summary.get('execution_time', 0):.1f}秒")
        
        # 显示智能体结果
        agent_results = result.get('agent_results', {})
        print(f"\n🤖 智能体执行结果:")
        for agent_id, agent_result in agent_results.items():
            execution_time = agent_result.get('execution_time', 0)
            result_length = len(str(agent_result.get('result', '')))
            print(f"   - {agent_id}: {execution_time:.1f}秒, {result_length}字符")
        
        print("=" * 80)
        
        # 分析协调结果
        coordination_result = result.get('coordination_result', '')
        
        # 检查是否包含协调决策的证据
        coordination_indicators = [
            "assign_task_to_agent", "analyze_agent_result", 
            "check_task_completion", "query_agent_status",
            "分配", "分析", "检查", "查询"
        ]
        
        found_indicators = [indicator for indicator in coordination_indicators 
                          if indicator in coordination_result.lower()]
        
        if found_indicators:
            print(f"🧠 发现协调决策证据: {found_indicators}")
        else:
            print("⚠️ 未发现明显的协调决策证据")
        
        return {
            "success": True,
            "execution_time": execution_time,
            "result": result,
            "coordination_evidence": found_indicators
        }
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e)
        }


async def test_llm_coordinator_complex():
    """测试LLM协调智能体复杂任务处理"""
    
    logger = get_test_logger()
    logger.info("🧠 开始测试LLM协调智能体复杂任务处理")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        
        # 创建并注册工作智能体（仅限实际存在的两个智能体）
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_reviewer_agent)
        
        # 生成唯一的对话ID
        conversation_id = f"test_complex_coordination_{int(time.time())}"
        
        # 复杂测试任务
        complex_request = """
请设计一个完整的ALU（算术逻辑单元）系统，要求：

1. 设计阶段：
   - 支持8种基本运算（加、减、与、或、异或、左移、右移、比较）
   - 包含16位数据输入和输出
   - 提供零标志、进位标志、溢出标志
   - 使用参数化设计，支持不同位宽

2. 验证阶段：
   - 生成全面的测试台
   - 包含边界条件测试
   - 验证所有运算功能
   - 进行仿真验证

3. 质量保证：
   - 代码审查和优化
   - 性能分析
   - 文档生成

请确保整个流程的质量和完整性。
"""
        
        logger.info(f"📋 复杂测试请求: {complex_request[:200]}...")
        logger.info(f"🔗 对话ID: {conversation_id}")
        
        # 执行协调任务
        start_time = time.time()
        
        result = await coordinator.coordinate_task(
            user_request=complex_request,
            conversation_id=conversation_id,
            max_iterations=20
        )
        
        execution_time = time.time() - start_time
        
        # 显示复杂任务结果
        print("\n" + "=" * 80)
        print("🧠 复杂任务协调测试结果")
        print("=" * 80)
        print(f"✅ 执行时间: {execution_time:.1f}秒")
        print(f"🔗 对话ID: {conversation_id}")
        print(f"📊 任务ID: {result.get('task_id', 'unknown')}")
        
        # 分析协调策略
        coordination_result = result.get('coordination_result', '')
        
        # 检查多阶段协调
        stage_indicators = [
            "设计阶段", "验证阶段", "质量保证", "多阶段", "迭代",
            "design phase", "verification phase", "quality assurance"
        ]
        
        found_stages = [indicator for indicator in stage_indicators 
                       if indicator in coordination_result.lower()]
        
        if found_stages:
            print(f"🔄 发现多阶段协调: {found_stages}")
        else:
            print("⚠️ 未发现明显的多阶段协调")
        
        # 显示智能体协作情况
        agent_results = result.get('agent_results', {})
        print(f"\n🤝 智能体协作情况:")
        for agent_id, agent_result in agent_results.items():
            execution_time = agent_result.get('execution_time', 0)
            result_length = len(str(agent_result.get('result', '')))
            print(f"   - {agent_id}: {execution_time:.1f}秒, {result_length}字符")
        
        print("=" * 80)
        
        return {
            "success": True,
            "execution_time": execution_time,
            "result": result,
            "stage_evidence": found_stages
        }
        
    except Exception as e:
        logger.error(f"❌ 复杂任务测试失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def test_llm_coordinator_context_preservation():
    """测试LLM协调智能体的上下文保持功能"""
    
    logger = get_test_logger()
    logger.info("🧠 开始测试LLM协调智能体上下文保持功能")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        
        # 创建并注册工作智能体（仅限实际存在的两个智能体）
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_reviewer_agent)
        
        # 使用同一个对话ID进行多轮交互
        conversation_id = f"test_context_preservation_{int(time.time())}"
        
        # 第一轮：设计任务
        design_request = """
请设计一个4位计数器模块，包含：
1. 时钟输入和复位输入
2. 计数输出
3. 使能控制
4. 溢出标志
"""
        
        logger.info(f"📋 第一轮请求（设计）: {design_request}")
        
        result1 = await coordinator.coordinate_task(
            user_request=design_request,
            conversation_id=conversation_id,
            max_iterations=10
        )
        
        # 第二轮：基于第一轮结果进行改进
        improvement_request = """
基于之前的设计，请进行以下改进：
1. 添加参数化支持，支持不同位宽
2. 增加同步复位功能
3. 添加计数方向控制（向上/向下）
4. 生成相应的测试台进行验证
"""
        
        logger.info(f"📋 第二轮请求（改进）: {improvement_request}")
        
        result2 = await coordinator.coordinate_task(
            user_request=improvement_request,
            conversation_id=conversation_id,
            max_iterations=10
        )
        
        # 第三轮：质量检查
        quality_request = """
请对之前的设计进行全面的质量检查：
1. 代码规范检查
2. 功能完整性验证
3. 性能优化建议
4. 文档完善
"""
        
        logger.info(f"📋 第三轮请求（质量检查）: {quality_request}")
        
        result3 = await coordinator.coordinate_task(
            user_request=quality_request,
            conversation_id=conversation_id,
            max_iterations=10
        )
        
        # 分析上下文保持效果
        print("\n" + "=" * 80)
        print("🧠 上下文保持测试结果")
        print("=" * 80)
        print(f"🔗 对话ID: {conversation_id}")
        
        # 检查每轮的结果
        results = [result1, result2, result3]
        total_time = sum(result.get('execution_summary', {}).get('execution_time', 0) for result in results)
        
        print(f"⏱️ 总执行时间: {total_time:.1f}秒")
        
        for i, result in enumerate(results, 1):
            task_id = result.get('task_id', 'unknown')
            iterations = result.get('execution_summary', {}).get('total_iterations', 0)
            agents = result.get('execution_summary', {}).get('assigned_agents', [])
            print(f"📊 第{i}轮: 任务{task_id}, {iterations}次迭代, 智能体: {', '.join(agents)}")
        
        # 检查上下文连续性
        context_indicators = [
            "基于之前", "之前的设计", "之前的结果", "继续", "改进",
            "based on previous", "previous design", "continue", "improve"
        ]
        
        all_results = [result.get('coordination_result', '') for result in results]
        context_evidence = []
        
        for i, result_text in enumerate(all_results[1:], 2):  # 从第2轮开始检查
            found = [indicator for indicator in context_indicators 
                    if indicator in result_text.lower()]
            if found:
                context_evidence.append(f"第{i}轮: {found}")
        
        if context_evidence:
            print(f"🧠 发现上下文连续性证据:")
            for evidence in context_evidence:
                print(f"   - {evidence}")
        else:
            print("⚠️ 未发现明显的上下文连续性证据")
        
        print("=" * 80)
        
        return {
            "success": True,
            "total_time": total_time,
            "results": results,
            "context_evidence": context_evidence
        }
        
    except Exception as e:
        logger.error(f"❌ 上下文保持测试失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def test_llm_coordinator_agent_selection():
    """测试LLM协调智能体的智能体选择功能"""
    
    logger = get_test_logger()
    logger.info("🎯 开始测试LLM协调智能体智能体选择功能")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        
        # 创建并注册工作智能体（仅限实际存在的两个智能体）
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_reviewer_agent)
        
        # 测试不同类型的任务
        test_tasks = [
            {
                "name": "设计任务",
                "request": "设计一个8位乘法器模块",
                "expected_agent": "enhanced_real_verilog_agent"
            },
            {
                "name": "验证任务", 
                "request": "为乘法器生成测试台并进行仿真验证",
                "expected_agent": "enhanced_real_code_review_agent"
            },
            {
                "name": "分析任务",
                "request": "分析代码质量并提供优化建议",
                "expected_agent": "enhanced_real_code_review_agent"
            }
        ]
        
        results = []
        
        for i, task in enumerate(test_tasks, 1):
            logger.info(f"📋 测试任务{i}: {task['name']}")
            
            conversation_id = f"test_agent_selection_{i}_{int(time.time())}"
            
            result = await coordinator.coordinate_task(
                user_request=task["request"],
                conversation_id=conversation_id,
                max_iterations=8
            )
            
            # 分析选择的智能体
            assigned_agents = result.get('execution_summary', {}).get('assigned_agents', [])
            expected_agent = task["expected_agent"]
            
            selection_correct = expected_agent in assigned_agents
            
            results.append({
                "task_name": task["name"],
                "expected_agent": expected_agent,
                "assigned_agents": assigned_agents,
                "selection_correct": selection_correct,
                "result": result
            })
            
            logger.info(f"🎯 任务{i}结果: 期望{expected_agent}, 实际{assigned_agents}, 正确{selection_correct}")
        
        # 显示智能体选择结果
        print("\n" + "=" * 80)
        print("🎯 智能体选择测试结果")
        print("=" * 80)
        
        correct_selections = sum(1 for r in results if r["selection_correct"])
        total_tasks = len(results)
        
        print(f"📊 选择准确率: {correct_selections}/{total_tasks} ({correct_selections/total_tasks*100:.1f}%)")
        
        for result in results:
            status = "✅" if result["selection_correct"] else "❌"
            print(f"{status} {result['task_name']}: 期望{result['expected_agent']}, 实际{result['assigned_agents']}")
        
        print("=" * 80)
        
        return {
            "success": True,
            "results": results,
            "accuracy": correct_selections / total_tasks
        }
        
    except Exception as e:
        logger.error(f"❌ 智能体选择测试失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    print("🧠 LLM协调智能体框架测试")
    print("=" * 50)
    
    # 运行基本功能测试
    print("\n1️⃣ 基本功能测试...")
    result1 = asyncio.run(test_llm_coordinator_basic())
    
    if result1["success"]:
        print("✅ 基本功能测试通过")
    else:
        print(f"❌ 基本功能测试失败: {result1['error']}")
    
    # 运行复杂任务测试
    print("\n2️⃣ 复杂任务测试...")
    try:
        result2 = asyncio.run(test_llm_coordinator_complex())
        if result2["success"]:
            print("✅ 复杂任务测试通过")
        else:
            print(f"❌ 复杂任务测试失败: {result2['error']}")
    except Exception as e:
        print(f"❌ 复杂任务测试异常: {str(e)}")
    
    # 运行上下文保持测试
    print("\n3️⃣ 上下文保持测试...")
    try:
        result3 = asyncio.run(test_llm_coordinator_context_preservation())
        if result3["success"]:
            print("✅ 上下文保持测试通过")
        else:
            print(f"❌ 上下文保持测试失败: {result3['error']}")
    except Exception as e:
        print(f"❌ 上下文保持测试异常: {str(e)}")
    
    # 运行智能体选择测试
    print("\n4️⃣ 智能体选择测试...")
    try:
        result4 = asyncio.run(test_llm_coordinator_agent_selection())
        if result4["success"]:
            print(f"✅ 智能体选择测试通过 (准确率: {result4['accuracy']*100:.1f}%)")
        else:
            print(f"❌ 智能体选择测试失败: {result4['error']}")
    except Exception as e:
        print(f"❌ 智能体选择测试异常: {str(e)}")
    
    print("\n🎉 所有测试完成！") 