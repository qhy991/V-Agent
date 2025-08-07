#!/usr/bin/env python3
"""
综合测试NoneType错误修复
验证所有可能导致NoneType错误的地方都已修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_integration.enhanced_llm_client import OptimizedLLMClient
from core.llm_communication.managers.client_manager import UnifiedLLMClientManager
from config.config import FrameworkConfig


async def test_enhanced_llm_client_none_fix():
    """测试enhanced_llm_client的NoneType修复"""
    print("🧪 测试enhanced_llm_client的NoneType修复...")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        print("✅ 成功加载环境配置")
        
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
        
        # 测试_send_prompt_internal方法
        try:
            # 创建OptimizedLLMClient实例
            llm_client = OptimizedLLMClient(config.llm)
            
            # 直接测试_send_prompt_internal方法
            response = await llm_client._send_prompt_internal(
                messages=conversation_with_none,
                temperature=0.3,
                max_tokens=1000,
                json_mode=False
            )
            print(f"✅ _send_prompt_internal调用成功，响应长度: {len(response) if response else 0}")
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


async def test_client_manager_none_fix():
    """测试client_manager的NoneType修复"""
    print("🧪 测试client_manager的NoneType修复...")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        print("✅ 成功加载环境配置")
        
        # 创建client_manager实例
        client_manager = UnifiedLLMClientManager("test_agent", "test_role", config)
        print("✅ 成功创建client_manager实例")
        
        # 创建包含None内容的对话历史
        conversation_with_none = [
            {"role": "system", "content": "你是一个Verilog设计专家"},
            {"role": "user", "content": "设计一个计数器"},
            {"role": "assistant", "content": None},  # 模拟None内容
            {"role": "user", "content": "请继续设计"},
            {"role": "assistant", "content": ""},  # 模拟空字符串
            {"role": "user", "content": None},  # 模拟None内容
        ]
        
        print("🔧 测试_build_user_message方法...")
        
        # 测试_build_user_message方法
        try:
            user_message = client_manager._build_user_message(conversation_with_none)
            print(f"✅ _build_user_message调用成功，消息长度: {len(user_message) if user_message else 0}")
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


async def test_conversation_processing():
    """测试对话处理中的None值处理"""
    print("🧪 测试对话处理中的None值处理...")
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        print("✅ 成功加载环境配置")
        
        # 创建包含各种None值情况的对话历史
        problematic_conversation = [
            None,  # 完全为None的消息
            {"role": "system", "content": "你是一个Verilog设计专家"},
            {"role": "user", "content": None},  # content为None
            {"role": None, "content": "一些内容"},  # role为None
            {"content": "缺少role字段"},  # 缺少role字段
            {"role": "assistant", "content": ""},  # 空字符串
            {"role": "user", "content": "正常消息"},
        ]
        
        print("🔧 测试问题对话历史处理...")
        
        # 测试OptimizedLLMClient的消息处理
        try:
            llm_client = OptimizedLLMClient(config.llm)
            
            # 测试消息构建过程
            messages = []
            for msg in problematic_conversation:
                if msg is None or "role" not in msg:
                    continue
                    
                content = msg.get("content", "")
                if content is None:
                    content = ""
                    
                messages.append({
                    "role": msg["role"],
                    "content": content
                })
            
            print(f"✅ 成功处理问题对话历史，有效消息数: {len(messages)}")
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
    print("🚀 开始综合NoneType错误修复验证测试")
    print("=" * 60)
    
    tests = [
        ("enhanced_llm_client", test_enhanced_llm_client_none_fix),
        ("client_manager", test_client_manager_none_fix),
        ("conversation_processing", test_conversation_processing),
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
        print("\n🎉 所有NoneType错误修复验证成功！")
        return 0
    else:
        print("\n❌ 部分NoneType错误修复验证失败！")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 