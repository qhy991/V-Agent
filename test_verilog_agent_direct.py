#!/usr/bin/env python3
"""
直接测试enhanced_real_verilog_agent的execute_enhanced_task方法
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
from core.types import TaskMessage
from config.config import FrameworkConfig


async def test_verilog_agent_execute_task():
    """直接测试Verilog智能体的execute_enhanced_task方法"""
    print("🧪 直接测试Verilog智能体的execute_enhanced_task方法...")
    
    try:
        # 创建智能体
        agent = EnhancedRealVerilogAgentRefactored()
        
        # 创建测试任务消息
        task_message = TaskMessage(
            task_id="test_task_001",
            sender_id="coordinator",
            receiver_id="enhanced_real_verilog_agent",
            message_type="task",
            content="设计一个4位计数器模块"
        )
        
        # 设置任务上下文
        agent.current_task_context = type('MockTaskContext', (), {
            'experiment_path': './test_experiment'
        })()
        
        # 测试execute_enhanced_task方法
        print("📋 调用execute_enhanced_task方法...")
        result = await agent.execute_enhanced_task(
            enhanced_prompt="设计一个4位计数器模块，包含时钟、复位、使能和计数输出",
            original_message=task_message,
            file_contents={}
        )
        
        print(f"✅ execute_enhanced_task调用成功，结果: {result}")
        return True
        
    except Exception as e:
        print(f"❌ execute_enhanced_task调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_verilog_agent_process_validation():
    """测试process_with_enhanced_validation方法"""
    print("🧪 测试process_with_enhanced_validation方法...")
    
    try:
        # 创建智能体
        agent = EnhancedRealVerilogAgentRefactored()
        
        # 测试process_with_enhanced_validation方法
        print("📋 调用process_with_enhanced_validation方法...")
        result = await agent.process_with_enhanced_validation(
            user_request="设计一个4位计数器模块",
            max_iterations=2
        )
        
        print(f"✅ process_with_enhanced_validation调用成功，结果: {result}")
        return True
        
    except Exception as e:
        print(f"❌ process_with_enhanced_validation调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_verilog_agent_llm_call():
    """测试LLM调用方法"""
    print("🧪 测试LLM调用方法...")
    
    try:
        # 创建智能体
        agent = EnhancedRealVerilogAgentRefactored()
        
        # 测试_call_llm_optimized_with_history方法
        print("📋 调用_call_llm_optimized_with_history方法...")
        result = await agent._call_llm_optimized_with_history(
            user_request="设计一个4位计数器模块",
            conversation_history=[],
            is_first_call=True
        )
        
        print(f"✅ _call_llm_optimized_with_history调用成功，结果长度: {len(result) if result else 0}")
        return True
        
    except Exception as e:
        print(f"❌ _call_llm_optimized_with_history调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🚀 开始直接测试enhanced_real_verilog_agent...")
    
    # 测试1：LLM调用
    test1_result = await test_verilog_agent_llm_call()
    
    # 测试2：process_with_enhanced_validation
    test2_result = await test_verilog_agent_process_validation()
    
    # 测试3：execute_enhanced_task
    test3_result = await test_verilog_agent_execute_task()
    
    if test1_result and test2_result and test3_result:
        print("🎉 所有测试通过！enhanced_real_verilog_agent工作正常")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 