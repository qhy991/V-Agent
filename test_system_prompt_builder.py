#!/usr/bin/env python3
"""
System Prompt构建器测试
验证新的System Prompt构建器功能
"""

import asyncio
import sys
from typing import Set

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试System Prompt构建器基础功能...")
    
    try:
        from core.llm_communication import SystemPromptBuilder, CallType
        from core.schema_system.enums import AgentCapability
        
        # 创建构建器
        builder = SystemPromptBuilder()
        
        print("✅ System Prompt构建器创建成功")
        print(f"📊 模板统计: {builder.get_template_stats()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_verilog_designer_prompt():
    """测试Verilog设计师Prompt生成"""
    print("\n🧪 测试Verilog设计师Prompt生成...")
    
    try:
        from core.llm_communication import SystemPromptBuilder, CallType
        from core.schema_system.enums import AgentCapability
        
        builder = SystemPromptBuilder()
        
        # 生成Verilog设计师Prompt
        prompt = await builder.build_system_prompt(
            role="verilog_designer",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_verilog_agent",
            capabilities={AgentCapability.CODE_GENERATION, AgentCapability.MODULE_DESIGN}
        )
        
        print(f"✅ Verilog设计师Prompt生成成功，长度: {len(prompt)} 字符")
        print(f"📝 Prompt预览: {prompt[:300]}...")
        
        # 验证内容
        assert "Verilog硬件设计专家" in prompt
        assert "代码生成能力" in prompt
        assert "模块设计能力" in prompt
        assert "Function Calling模式" in prompt
        
        return True
        
    except Exception as e:
        print(f"❌ Verilog设计师Prompt测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_code_reviewer_prompt():
    """测试代码审查师Prompt生成"""
    print("\n🧪 测试代码审查师Prompt生成...")
    
    try:
        from core.llm_communication import SystemPromptBuilder, CallType
        from core.schema_system.enums import AgentCapability
        
        builder = SystemPromptBuilder()
        
        # 生成代码审查师Prompt
        prompt = await builder.build_system_prompt(
            role="code_reviewer",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_reviewer_agent",
            capabilities={AgentCapability.CODE_REVIEW, AgentCapability.TEST_GENERATION}
        )
        
        print(f"✅ 代码审查师Prompt生成成功，长度: {len(prompt)} 字符")
        print(f"📝 Prompt预览: {prompt[:300]}...")
        
        # 验证内容
        assert "硬件代码审查专家" in prompt
        assert "代码审查能力" in prompt
        assert "测试生成能力" in prompt
        assert "Function Calling模式" in prompt
        
        return True
        
    except Exception as e:
        print(f"❌ 代码审查师Prompt测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_coordinator_prompt():
    """测试协调器Prompt生成"""
    print("\n🧪 测试协调器Prompt生成...")
    
    try:
        from core.llm_communication import SystemPromptBuilder, CallType
        from core.schema_system.enums import AgentCapability
        
        builder = SystemPromptBuilder()
        
        # 生成协调器Prompt
        prompt = await builder.build_system_prompt(
            role="coordinator",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_coordinator_agent",
            capabilities={AgentCapability.TASK_COORDINATION, AgentCapability.WORKFLOW_MANAGEMENT}
        )
        
        print(f"✅ 协调器Prompt生成成功，长度: {len(prompt)} 字符")
        print(f"📝 Prompt预览: {prompt[:300]}...")
        
        # 验证内容
        assert "智能任务协调专家" in prompt
        assert "任务管理能力" in prompt
        assert "工作流管理能力" in prompt
        assert "Function Calling模式" in prompt
        
        return True
        
    except Exception as e:
        print(f"❌ 协调器Prompt测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_caching_functionality():
    """测试缓存功能"""
    print("\n🧪 测试缓存功能...")
    
    try:
        from core.llm_communication import SystemPromptBuilder, CallType
        from core.schema_system.enums import AgentCapability
        
        builder = SystemPromptBuilder()
        
        # 第一次生成
        prompt1 = await builder.build_system_prompt(
            role="verilog_designer",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_agent",
            capabilities={AgentCapability.CODE_GENERATION}
        )
        
        # 第二次生成（应该使用缓存）
        prompt2 = await builder.build_system_prompt(
            role="verilog_designer",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_agent",
            capabilities={AgentCapability.CODE_GENERATION}
        )
        
        # 验证缓存
        assert prompt1 == prompt2
        stats = builder.get_template_stats()
        assert stats["cached_prompts"] > 0
        
        print(f"✅ 缓存功能正常，缓存数量: {stats['cached_prompts']}")
        
        # 测试清除缓存
        builder.clear_cache()
        stats_after_clear = builder.get_template_stats()
        assert stats_after_clear["cached_prompts"] == 0
        
        print("✅ 缓存清除功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理...")
    
    try:
        from core.llm_communication import SystemPromptBuilder, CallType
        
        builder = SystemPromptBuilder()
        
        # 测试未知角色
        try:
            await builder.build_system_prompt(
                role="unknown_role",
                call_type=CallType.FUNCTION_CALLING,
                agent_id="test_agent"
            )
            print("⚠️ 应该检测到未知角色错误")
        except ValueError as e:
            print(f"✅ 正确捕获未知角色错误: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始System Prompt构建器测试...\n")
    
    # 基础功能测试
    basic_success = test_basic_functionality()
    
    # Verilog设计师Prompt测试
    verilog_success = await test_verilog_designer_prompt()
    
    # 代码审查师Prompt测试
    reviewer_success = await test_code_reviewer_prompt()
    
    # 协调器Prompt测试
    coordinator_success = await test_coordinator_prompt()
    
    # 缓存功能测试
    cache_success = await test_caching_functionality()
    
    # 错误处理测试
    error_success = await test_error_handling()
    
    # 总结
    print("\n" + "="*60)
    print("📋 System Prompt构建器测试结果总结:")
    print(f"   基础功能: {'✅ 通过' if basic_success else '❌ 失败'}")
    print(f"   Verilog设计师: {'✅ 通过' if verilog_success else '❌ 失败'}")
    print(f"   代码审查师: {'✅ 通过' if reviewer_success else '❌ 失败'}")
    print(f"   协调器: {'✅ 通过' if coordinator_success else '❌ 失败'}")
    print(f"   缓存功能: {'✅ 通过' if cache_success else '❌ 失败'}")
    print(f"   错误处理: {'✅ 通过' if error_success else '❌ 失败'}")
    
    all_success = all([basic_success, verilog_success, reviewer_success, 
                      coordinator_success, cache_success, error_success])
    
    if all_success:
        print("\n🎉 所有System Prompt构建器测试通过！")
        print("💡 新的System Prompt构建器已准备就绪。")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 