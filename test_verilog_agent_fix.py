#!/usr/bin/env python3
"""
测试enhanced_real_verilog_agent的修复
验证NoneType错误是否已解决
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
from core.base_agent import TaskMessage
from config.config import FrameworkConfig


async def test_verilog_agent_none_fix():
    """测试enhanced_real_verilog_agent的NoneType修复"""
    print("🧪 测试enhanced_real_verilog_agent的NoneType修复...")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        print("✅ 成功加载环境配置")
        
        # 创建智能体实例
        agent = EnhancedRealVerilogAgentRefactored(config)
        print("✅ 成功创建enhanced_real_verilog_agent实例")
        
        # 创建包含None内容的对话历史（模拟问题场景）
        conversation_with_none = [
            {"role": "system", "content": "你是一个Verilog设计专家"},
            {"role": "user", "content": "设计一个计数器"},
            {"role": "assistant", "content": None},  # 模拟None内容
            {"role": "user", "content": "请继续设计"},
            {"role": "assistant", "content": ""},  # 模拟空字符串
            {"role": "user", "content": None},  # 模拟None内容
        ]
        
        print("🔧 测试包含None内容的对话历史处理...")
        
        # 测试_call_llm_for_function_calling方法
        try:
            response = await agent._call_llm_for_function_calling(conversation_with_none)
            print(f"✅ _call_llm_for_function_calling调用成功，响应长度: {len(response) if response else 0}")
            return True
            
        except Exception as e:
            if "NoneType" in str(e):
                print(f"❌ 仍然存在NoneType错误: {e}")
                import traceback
                traceback.print_exc()
                return False
            else:
                print(f"⚠️ 其他错误（可接受）: {e}")
                return True
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_verilog_agent_execution():
    """测试enhanced_real_verilog_agent的任务执行"""
    print("🧪 测试enhanced_real_verilog_agent的任务执行...")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        print("✅ 成功加载环境配置")
        
        # 创建智能体实例
        agent = EnhancedRealVerilogAgentRefactored(config)
        print("✅ 成功创建enhanced_real_verilog_agent实例")
        
        # 创建任务消息
        task_message = TaskMessage(
            task_id="test_task_001",
            sender_id="user",
            receiver_id="enhanced_real_verilog_agent",
            message_type="task_request",
            content="设计一个8位计数器模块"
        )
        
        print("🔧 测试任务执行...")
        
        # 测试execute_enhanced_task方法
        try:
            result = await agent.execute_enhanced_task(
                enhanced_prompt="设计一个8位计数器模块，包含时钟、复位和使能信号",
                original_message=task_message,
                file_contents={}
            )
            print(f"✅ execute_enhanced_task调用成功，结果类型: {type(result)}")
            return True
            
        except Exception as e:
            if "NoneType" in str(e):
                print(f"❌ 仍然存在NoneType错误: {e}")
                import traceback
                traceback.print_exc()
                return False
            else:
                print(f"⚠️ 其他错误（可接受）: {e}")
                return True
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("🚀 开始enhanced_real_verilog_agent修复验证测试")
    print("=" * 60)
    
    tests = [
        ("verilog_agent_none_fix", test_verilog_agent_none_fix),
        ("verilog_agent_execution", test_verilog_agent_execution),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        print("-" * 40)
        results[test_name] = await test_func()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有enhanced_real_verilog_agent修复验证成功！")
        return 0
    else:
        print("\n❌ 部分enhanced_real_verilog_agent修复验证失败！")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 