#!/usr/bin/env python3
"""
LLM协调智能体框架简单示例

Simple Example for LLM Coordinator Agent Framework
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent


async def simple_example():
    """简单的LLM协调智能体使用示例"""
    
    print("🧠 LLM协调智能体框架简单示例")
    print("=" * 50)
    
    try:
        # 1. 初始化配置
        print("1️⃣ 初始化配置...")
        config = FrameworkConfig.from_env()
        print("✅ 配置初始化完成")
        
        # 2. 创建协调智能体
        print("2️⃣ 创建协调智能体...")
        coordinator = LLMCoordinatorAgent(config)
        print("✅ 协调智能体创建完成")
        
        # 3. 创建并注册工作智能体
        print("3️⃣ 创建并注册工作智能体...")
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_reviewer_agent)
        print("✅ 智能体注册完成")
        
        # 4. 显示已注册的智能体
        print("\n📋 已注册的智能体:")
        registered_agents = coordinator.get_registered_agents()
        for agent_id, agent_info in registered_agents.items():
            capabilities = [cap.value for cap in agent_info.capabilities]
            print(f"   - {agent_id}: {agent_info.specialty}")
            print(f"     能力: {', '.join(capabilities)}")
        
        # 5. 执行协调任务
        print("\n4️⃣ 执行协调任务...")
        test_request = """
请设计一个4位加法器模块，包含：
1. 基本的加法功能
2. 进位输出
3. 相应的测试台和仿真验证

请确保代码质量和功能完整性。
"""
        
        print(f"📋 任务请求: {test_request.strip()}")
        
        result = await coordinator.coordinate_task(
            user_request=test_request,
            conversation_id="simple_example_123",
            max_iterations=10
        )
        
        # 6. 显示结果
        print("\n5️⃣ 任务执行结果:")
        if result.get("success"):
            print("✅ 任务执行成功")
            
            execution_summary = result.get("execution_summary", {})
            print(f"   - 总迭代次数: {execution_summary.get('total_iterations', 0)}")
            print(f"   - 分配的智能体: {', '.join(execution_summary.get('assigned_agents', []))}")
            print(f"   - 执行时间: {execution_summary.get('execution_time', 0):.1f}秒")
            
            # 显示智能体结果
            agent_results = result.get("agent_results", {})
            print(f"\n🤖 智能体执行结果:")
            for agent_id, agent_result in agent_results.items():
                execution_time = agent_result.get("execution_time", 0)
                result_length = len(str(agent_result.get("result", "")))
                print(f"   - {agent_id}: {execution_time:.1f}秒, {result_length}字符")
            
            # 显示协调结果摘要
            coordination_result = result.get("coordination_result", "")
            print(f"\n🧠 协调结果摘要:")
            print(f"   - 结果长度: {len(coordination_result)}字符")
            print(f"   - 前200字符: {coordination_result[:200]}...")
            
        else:
            print("❌ 任务执行失败")
            print(f"   错误: {result.get('error', '未知错误')}")
        
        print("\n🎉 示例执行完成！")
        
    except Exception as e:
        print(f"❌ 示例执行失败: {str(e)}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")


async def multi_turn_example():
    """多轮对话示例"""
    
    print("\n🔄 多轮对话示例")
    print("=" * 50)
    
    try:
        # 初始化
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_reviewer_agent)
        
        conversation_id = "multi_turn_example"
        
        # 第一轮：设计任务
        print("📋 第一轮：设计任务")
        result1 = await coordinator.coordinate_task(
            user_request="设计一个8位计数器模块",
            conversation_id=conversation_id,
            max_iterations=8
        )
        
        print(f"   结果: {'成功' if result1.get('success') else '失败'}")
        
        # 第二轮：改进任务
        print("📋 第二轮：改进任务")
        result2 = await coordinator.coordinate_task(
            user_request="基于之前的设计，添加使能控制和同步复位功能",
            conversation_id=conversation_id,
            max_iterations=8
        )
        
        print(f"   结果: {'成功' if result2.get('success') else '失败'}")
        
        # 第三轮：验证任务
        print("📋 第三轮：验证任务")
        result3 = await coordinator.coordinate_task(
            user_request="对设计进行全面的测试验证",
            conversation_id=conversation_id,
            max_iterations=8
        )
        
        print(f"   结果: {'成功' if result3.get('success') else '失败'}")
        
        # 显示多轮结果
        results = [result1, result2, result3]
        total_time = sum(result.get('execution_summary', {}).get('execution_time', 0) for result in results)
        
        print(f"\n📊 多轮对话统计:")
        print(f"   - 总执行时间: {total_time:.1f}秒")
        print(f"   - 成功轮次: {sum(1 for r in results if r.get('success'))}/{len(results)}")
        
        print("🎉 多轮对话示例完成！")
        
    except Exception as e:
        print(f"❌ 多轮对话示例失败: {str(e)}")


if __name__ == "__main__":
    print("🚀 开始LLM协调智能体示例")
    
    # 运行简单示例
    asyncio.run(simple_example())
    
    # 运行多轮对话示例
    asyncio.run(multi_turn_example())
    
    print("\n🎉 所有示例执行完成！") 