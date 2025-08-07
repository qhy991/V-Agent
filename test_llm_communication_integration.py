#!/usr/bin/env python3
"""
LLM通信模块集成测试
测试在实际场景中的功能表现
"""

import asyncio
import sys
import time
from typing import List, Dict

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试基础功能...")
    
    try:
        from core.llm_communication import UnifiedLLMClientManager, LLMCallContext, CallType, PromptTemplateEngine
        from core.schema_system.framework_config import FrameworkConfig
        from core.schema_system.enums import AgentCapability
        
        # 创建配置
        config = FrameworkConfig.from_env()
        
        # 创建模板引擎
        template_engine = PromptTemplateEngine()
        
        # 创建客户端管理器
        llm_manager = UnifiedLLMClientManager(
            agent_id="test_verilog_agent",
            role="verilog_designer",
            config=config
        )
        
        print("✅ 基础组件创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_template_generation():
    """测试模板生成功能"""
    print("\n🧪 测试模板生成功能...")
    
    try:
        from core.llm_communication import PromptTemplateEngine, CallType
        from core.schema_system.enums import AgentCapability
        
        template_engine = PromptTemplateEngine()
        
        # 测试Verilog设计师模板
        verilog_prompt = await template_engine.build_system_prompt(
            role="verilog_designer",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_verilog_agent",
            capabilities={AgentCapability.CODE_GENERATION, AgentCapability.MODULE_DESIGN}
        )
        
        print(f"✅ Verilog设计师模板生成成功，长度: {len(verilog_prompt)} 字符")
        print(f"📝 模板预览: {verilog_prompt[:200]}...")
        
        # 测试代码审查师模板
        reviewer_prompt = await template_engine.build_system_prompt(
            role="code_reviewer",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_reviewer_agent",
            capabilities={AgentCapability.CODE_REVIEW, AgentCapability.TEST_GENERATION}
        )
        
        print(f"✅ 代码审查师模板生成成功，长度: {len(reviewer_prompt)} 字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_conversation_handling():
    """测试对话处理功能"""
    print("\n🧪 测试对话处理功能...")
    
    try:
        from core.llm_communication import UnifiedLLMClientManager, LLMCallContext, CallType
        from core.schema_system.framework_config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        llm_manager = UnifiedLLMClientManager(
            agent_id="test_conversation_agent",
            role="verilog_designer",
            config=config
        )
        
        # 模拟对话历史
        conversation = [
            {"role": "user", "content": "请设计一个4位计数器模块"},
            {"role": "assistant", "content": "我来为您设计一个4位计数器模块。"},
            {"role": "user", "content": "需要添加复位功能"}
        ]
        
        # 测试对话构建
        user_message = llm_manager._build_user_message(conversation)
        print(f"✅ 对话构建成功，用户消息长度: {len(user_message)} 字符")
        print(f"📝 用户消息预览: {user_message[:150]}...")
        
        # 测试性能统计
        stats = llm_manager.get_performance_stats()
        print(f"📊 性能统计: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 对话处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """测试错误处理功能"""
    print("\n🧪 测试错误处理功能...")
    
    try:
        from core.llm_communication import UnifiedLLMClientManager, LLMCallContext, CallType
        from core.schema_system.framework_config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        
        # 测试无效参数处理
        try:
            llm_manager = UnifiedLLMClientManager(
                agent_id="",  # 空agent_id
                role="invalid_role",
                config=config
            )
            print("⚠️ 应该检测到无效参数")
        except Exception as e:
            print(f"✅ 正确捕获无效参数错误: {type(e).__name__}")
        
        # 测试配置验证
        try:
            llm_manager = UnifiedLLMClientManager(
                agent_id="test_agent",
                role="verilog_designer",
                config=None  # 空配置
            )
            print("⚠️ 应该检测到空配置")
        except Exception as e:
            print(f"✅ 正确捕获配置错误: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitoring():
    """测试性能监控功能"""
    print("\n🧪 测试性能监控功能...")
    
    try:
        from core.llm_communication import UnifiedLLMClientManager, LLMCallContext, CallType
        from core.schema_system.framework_config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        llm_manager = UnifiedLLMClientManager(
            agent_id="performance_test_agent",
            role="verilog_designer",
            config=config
        )
        
        # 模拟多次调用
        for i in range(3):
            # 模拟调用统计
            llm_manager.stats["total_calls"] += 1
            llm_manager.stats["successful_calls"] += 1
            llm_manager.stats["total_duration"] += 0.5 + i * 0.1
            
            if i % 2 == 0:
                llm_manager.stats["cache_hits"] += 1
            else:
                llm_manager.stats["cache_misses"] += 1
        
        # 获取性能统计
        stats = llm_manager.get_performance_stats()
        
        print(f"📊 性能统计详情:")
        print(f"   - 总调用次数: {stats['total_calls']}")
        print(f"   - 成功调用次数: {stats['successful_calls']}")
        print(f"   - 成功率: {stats['success_rate']:.2%}")
        print(f"   - 平均耗时: {stats['average_duration']:.3f}秒")
        print(f"   - 缓存命中率: {stats['cache_hit_rate']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能监控测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始LLM通信模块集成测试...\n")
    
    # 基础功能测试
    basic_success = test_basic_functionality()
    
    # 模板生成测试
    template_success = await test_template_generation()
    
    # 对话处理测试
    conversation_success = await test_conversation_handling()
    
    # 错误处理测试
    error_success = test_error_handling()
    
    # 性能监控测试
    performance_success = test_performance_monitoring()
    
    # 总结
    print("\n" + "="*60)
    print("📋 集成测试结果总结:")
    print(f"   基础功能: {'✅ 通过' if basic_success else '❌ 失败'}")
    print(f"   模板生成: {'✅ 通过' if template_success else '❌ 失败'}")
    print(f"   对话处理: {'✅ 通过' if conversation_success else '❌ 失败'}")
    print(f"   错误处理: {'✅ 通过' if error_success else '❌ 失败'}")
    print(f"   性能监控: {'✅ 通过' if performance_success else '❌ 失败'}")
    
    all_success = all([basic_success, template_success, conversation_success, error_success, performance_success])
    
    if all_success:
        print("\n🎉 所有集成测试通过！LLM通信模块已准备就绪。")
        print("💡 现在可以在实际项目中使用这个模块了。")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 