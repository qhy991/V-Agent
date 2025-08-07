#!/usr/bin/env python3
"""
简单的LLM通信模块测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        from core.llm_communication import UnifiedLLMClientManager, LLMCallContext, CallType, PromptTemplateEngine
        print("✅ 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_engine():
    """测试模板引擎"""
    print("\n🧪 测试模板引擎...")
    
    try:
        from core.llm_communication import PromptTemplateEngine, CallType
        from core.schema_system.enums import AgentCapability
        
        # 创建模板引擎
        template_engine = PromptTemplateEngine()
        
        # 测试模板加载
        print(f"✅ 模板引擎创建成功")
        print(f"📊 模板统计: {template_engine.get_template_stats()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_client_manager():
    """测试客户端管理器"""
    print("\n🧪 测试客户端管理器...")
    
    try:
        from core.llm_communication import UnifiedLLMClientManager, LLMCallContext, CallType
        from core.schema_system.framework_config import FrameworkConfig
        
        # 创建配置
        config = FrameworkConfig.from_env()
        
        # 创建客户端管理器
        llm_manager = UnifiedLLMClientManager(
            agent_id="test_agent",
            role="verilog_designer", 
            config=config
        )
        
        # 创建调用上下文
        context = LLMCallContext(
            conversation_id="test_conversation",
            agent_id="test_agent",
            role="verilog_designer",
            is_first_call=True,
            conversation_length=0,
            total_length=0
        )
        
        print(f"✅ 客户端管理器创建成功")
        print(f"📊 性能指标: {llm_manager.get_performance_stats()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 客户端管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始LLM通信模块测试...\n")
    
    # 测试导入
    import_success = test_imports()
    
    # 测试模板引擎
    template_success = test_template_engine()
    
    # 测试客户端管理器
    manager_success = test_client_manager()
    
    # 总结
    print("\n" + "="*50)
    print("📋 测试结果总结:")
    print(f"   模块导入: {'✅ 通过' if import_success else '❌ 失败'}")
    print(f"   模板引擎: {'✅ 通过' if template_success else '❌ 失败'}")
    print(f"   客户端管理器: {'✅ 通过' if manager_success else '❌ 失败'}")
    
    if import_success and template_success and manager_success:
        print("\n🎉 所有测试通过！LLM通信模块基础功能正常。")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)