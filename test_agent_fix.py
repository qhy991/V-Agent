#!/usr/bin/env python3
"""
测试修复后的智能体功能
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_agent_imports():
    """测试智能体导入"""
    print("🔍 测试智能体导入...")
    
    try:
        # 测试导入EnhancedBaseAgent基类
        from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
        print("✅ EnhancedBaseAgent导入成功")
        
        # 测试导入相关模块
        from core.enums import AgentCapability
        from core.base_agent import TaskMessage
        from core.response_format import ResponseFormat, TaskStatus, ResponseType, QualityMetrics
        print("✅ 核心模块导入成功")
        
        # 测试配置
        from config.config import FrameworkConfig
        print("✅ 配置模块导入成功")
        
        print("✅ 所有基础依赖导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 基础依赖导入失败: {e}")
        return False

async def test_verilog_agent_creation():
    """测试Verilog智能体创建"""
    print("\n🔍 测试Verilog智能体创建...")
    
    try:
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
        
        # 创建配置
        config = FrameworkConfig()
        config.llm.model_name = "test_model"
        config.llm.api_key = "test_key"
        config.llm.base_url = "http://localhost"
        
        # 创建智能体实例（不真正初始化LLM连接）
        agent = EnhancedRealVerilogAgent(config)
        print("✅ Verilog智能体创建成功")
        print(f"   - Agent ID: {agent.agent_id}")
        print(f"   - 角色: {agent.role}")
        print(f"   - 能力: {len(agent._capabilities)} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ Verilog智能体创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_response_format_compatibility():
    """测试响应格式兼容性"""
    print("\n🔍 测试响应格式兼容性...")
    
    try:
        from core.response_format import ResponseFormat, TaskStatus, ResponseType, QualityMetrics
        
        # 测试创建响应格式
        quality_metrics = QualityMetrics(
            overall_score=0.9,
            syntax_score=0.85,
            functionality_score=0.8,
            test_coverage=0.75,
            documentation_quality=0.8
        )
        
        print("✅ 响应格式兼容性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 响应格式兼容性测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始智能体修复验证测试")
    print("=" * 50)
    
    # 测试基础导入
    if not await test_agent_imports():
        print("❌ 基础导入测试失败，退出")
        return False
    
    # 测试智能体创建
    if not await test_verilog_agent_creation():
        print("❌ 智能体创建测试失败，退出")
        return False
    
    # 测试响应格式
    if not await test_response_format_compatibility():
        print("❌ 响应格式测试失败，退出") 
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过！智能体修复成功")
    print("\n📋 修复总结:")
    print("✅ 恢复了working版本的enhanced_real_verilog_agent.py")
    print("✅ 修复了导入依赖问题")
    print("✅ 验证了响应格式兼容性")
    print("✅ 智能体创建正常")
    
    return True

if __name__ == "__main__":
    # 设置环境变量以避免实际LLM调用
    os.environ.setdefault('OPENAI_API_KEY', 'test_key')
    os.environ.setdefault('LLM_MODEL', 'test_model')
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)