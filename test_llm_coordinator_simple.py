#!/usr/bin/env python3
"""
简化的LLM协调智能体测试

Simple LLM Coordinator Test
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


async def test_llm_coordinator_simple():
    """简化的LLM协调智能体测试"""
    
    logger = get_test_logger()
    logger.info("🚀 开始简化LLM协调智能体测试")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        
        # 创建并注册工作智能体
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer_agent = EnhancedRealCodeReviewAgent(config)
        
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(code_reviewer_agent)
        
        # 生成唯一的对话ID
        conversation_id = f"test_simple_{int(time.time())}"
        
        # 简单测试任务
        test_request = """
请设计一个4位加法器模块，包含：
1. 基本的加法功能
2. 进位输出
3. 相应的测试台

请确保代码质量。
"""
        
        logger.info(f"📋 测试请求: {test_request}")
        logger.info(f"🔗 对话ID: {conversation_id}")
        
        # 执行协调任务
        start_time = time.time()
        
        result = await coordinator.coordinate_task(
            user_request=test_request,
            conversation_id=conversation_id,
            max_iterations=5  # 减少迭代次数以加快测试
        )
        
        execution_time = time.time() - start_time
        
        # 显示结果
        print("\n" + "=" * 80)
        print("🎯 简化LLM协调智能体测试结果")
        print("=" * 80)
        print(f"✅ 执行时间: {execution_time:.1f}秒")
        print(f"🔗 对话ID: {conversation_id}")
        print(f"📊 任务ID: {result.get('task_id', 'unknown')}")
        print(f"🎭 协调结果长度: {len(result.get('coordination_result', ''))}字符")
        
        # 检查是否成功
        if result.get('success', False):
            print("✅ 测试成功完成")
            
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
        else:
            print(f"❌ 测试失败: {result.get('error', '未知错误')}")
        
        print("=" * 80)
        
        return {
            "success": result.get('success', False),
            "execution_time": execution_time,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    print("🧠 简化LLM协调智能体测试")
    print("=" * 50)
    
    # 运行简化测试
    result = asyncio.run(test_llm_coordinator_simple())
    
    if result["success"]:
        print("✅ 简化测试通过")
    else:
        print(f"❌ 简化测试失败: {result.get('error', '未知错误')}")
    
    print("\n🎉 测试完成！") 