#!/usr/bin/env python3
"""
测试enhanced_real_verilog_agent的修复
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

async def test_verilog_agent_basic():
    """测试enhanced_real_verilog_agent的基本功能"""
    print("🧪 开始测试enhanced_real_verilog_agent的基本功能...")
    
    try:
        # 创建智能体实例
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        print("✅ 智能体创建成功")
        
        # 创建测试任务
        task_message = TaskMessage(
            task_id="test_task_001",
            sender_id="test_user",
            receiver_id="enhanced_real_verilog_agent",
            message_type="task",
            content="请设计一个简单的8位计数器模块"
        )
        
        # 测试execute_enhanced_task方法
        result = await agent.execute_enhanced_task(
            enhanced_prompt="请设计一个简单的8位计数器模块",
            original_message=task_message,
            file_contents={}
        )
        
        print(f"✅ execute_enhanced_task执行完成")
        print(f"   成功: {result.get('success', False)}")
        print(f"   错误: {result.get('error', '无')}")
        
        if result.get('success'):
            print("🎉 测试通过！enhanced_real_verilog_agent可以正常工作")
        else:
            print(f"❌ 测试失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_verilog_agent_llm_call():
    """测试enhanced_real_verilog_agent的LLM调用"""
    print("\n🧪 开始测试enhanced_real_verilog_agent的LLM调用...")
    
    try:
        # 创建智能体实例
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 测试_call_llm_for_function_calling方法
        conversation = [
            {"role": "user", "content": "请分析这个设计需求：设计一个8位计数器"}
        ]
        
        response = await agent._call_llm_for_function_calling(conversation)
        
        print(f"✅ _call_llm_for_function_calling执行完成")
        print(f"   响应长度: {len(response) if response else 0}")
        print(f"   响应预览: {response[:200] if response else '无响应'}...")
        
    except Exception as e:
        print(f"❌ LLM调用测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_verilog_agent_optimized_call():
    """测试enhanced_real_verilog_agent的优化LLM调用"""
    print("\n🧪 开始测试enhanced_real_verilog_agent的优化LLM调用...")
    
    try:
        # 创建智能体实例
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        # 测试_call_llm_optimized_with_history方法
        user_request = "请设计一个8位计数器模块"
        conversation_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！我是Verilog设计助手，有什么可以帮助你的吗？"}
        ]
        
        response = await agent._call_llm_optimized_with_history(
            user_request=user_request,
            conversation_history=conversation_history,
            is_first_call=True
        )
        
        print(f"✅ _call_llm_optimized_with_history执行完成")
        print(f"   响应长度: {len(response) if response else 0}")
        print(f"   响应预览: {response[:200] if response else '无响应'}...")
        
    except Exception as e:
        print(f"❌ 优化LLM调用测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """主测试函数"""
    print("🚀 开始enhanced_real_verilog_agent修复验证测试")
    print("=" * 60)
    
    # 测试1：基本功能
    await test_verilog_agent_basic()
    
    # 测试2：LLM调用
    await test_verilog_agent_llm_call()
    
    # 测试3：优化LLM调用
    await test_verilog_agent_optimized_call()
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 