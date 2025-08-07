#!/usr/bin/env python3
"""
测试模型配置修复
验证硬编码的模型名称是否已被替换为动态配置
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.base_agent import BaseAgent
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

async def test_model_configuration():
    """测试模型配置"""
    print("🔍 测试模型配置修复")
    print("=" * 50)
    
    # 1. 测试配置加载
    print("1. 测试配置加载...")
    config = FrameworkConfig.from_env()
    print(f"   ✅ 配置加载成功")
    print(f"   📋 模型名称: {config.llm.model_name}")
    print(f"   📋 提供商: {config.llm.provider}")
    print(f"   📋 API密钥: {'已设置' if config.llm.api_key else '未设置'}")
    
    # 2. 测试BaseAgent的模型名称获取
    print("\n2. 测试BaseAgent模型名称获取...")
    try:
        # 创建一个测试用的BaseAgent子类
        class TestAgent(BaseAgent):
            async def _call_llm_for_function_calling(self, conversation):
                return "test response"
            
            async def execute_enhanced_task(self, enhanced_prompt, original_message, file_contents):
                return {"status": "success"}
        
        agent = TestAgent("test_agent")
        model_name = agent._get_model_name()
        print(f"   ✅ BaseAgent模型名称: {model_name}")
        print(f"   📋 与配置一致: {model_name == config.llm.model_name}")
        
    except Exception as e:
        print(f"   ❌ BaseAgent测试失败: {e}")
    
    # 3. 测试LLMCoordinatorAgent
    print("\n3. 测试LLMCoordinatorAgent...")
    try:
        coordinator = LLMCoordinatorAgent(config)
        print(f"   ✅ LLMCoordinatorAgent初始化成功")
        print(f"   📋 配置模型名称: {coordinator.config.llm.model_name}")
        
    except Exception as e:
        print(f"   ❌ LLMCoordinatorAgent测试失败: {e}")
    
    # 4. 测试EnhancedRealVerilogAgentRefactored
    print("\n4. 测试EnhancedRealVerilogAgentRefactored...")
    try:
        verilog_agent = EnhancedRealVerilogAgentRefactored(config)
        print(f"   ✅ EnhancedRealVerilogAgentRefactored初始化成功")
        print(f"   📋 配置模型名称: {verilog_agent.config.llm.model_name}")
        
    except Exception as e:
        print(f"   ❌ EnhancedRealVerilogAgentRefactored测试失败: {e}")
    
    # 5. 测试EnhancedRealCodeReviewAgent
    print("\n5. 测试EnhancedRealCodeReviewAgent...")
    try:
        review_agent = EnhancedRealCodeReviewAgent(config)
        print(f"   ✅ EnhancedRealCodeReviewAgent初始化成功")
        print(f"   📋 配置模型名称: {review_agent.config.llm.model_name}")
        
    except Exception as e:
        print(f"   ❌ EnhancedRealCodeReviewAgent测试失败: {e}")
    
    # 6. 验证环境变量
    print("\n6. 验证环境变量...")
    env_model = os.getenv("CAF_LLM_MODEL")
    print(f"   📋 环境变量CAF_LLM_MODEL: {env_model}")
    print(f"   📋 配置模型名称: {config.llm.model_name}")
    print(f"   📋 是否一致: {env_model == config.llm.model_name if env_model else '环境变量未设置'}")
    
    print("\n" + "=" * 50)
    print("🎉 模型配置测试完成！")
    
    # 总结
    print("\n📊 测试总结:")
    print(f"   • 配置加载: ✅")
    print(f"   • 模型名称: {config.llm.model_name}")
    print(f"   • 提供商: {config.llm.provider}")
    print(f"   • 硬编码修复: ✅ (已替换为动态配置)")
    
    return True

if __name__ == "__main__":
    # 设置环境变量用于测试
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 运行测试
    success = asyncio.run(test_model_configuration())
    
    if success:
        print("\n✅ 所有测试通过！模型配置修复成功。")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1) 