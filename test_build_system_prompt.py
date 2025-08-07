#!/usr/bin/env python3
"""
直接测试_build_enhanced_system_prompt方法
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent

async def test_build_system_prompt():
    """直接测试_build_enhanced_system_prompt方法"""
    print("🔍 直接测试_build_enhanced_system_prompt方法...")
    
    try:
        # 1. 加载配置
        print("📋 加载配置...")
        config = FrameworkConfig.from_env()
        print(f"✅ 配置加载成功")
        
        # 2. 创建LLMCoordinatorAgent
        print("\n🔧 创建LLMCoordinatorAgent...")
        coordinator = LLMCoordinatorAgent(config=config)
        print("✅ LLMCoordinatorAgent创建成功")
        
        # 3. 检查_capabilities
        print(f"\n🔍 检查_capabilities: {coordinator._capabilities}")
        
        # 4. 测试_build_enhanced_system_prompt方法
        print("\n📝 测试_build_enhanced_system_prompt方法...")
        try:
            system_prompt = await coordinator._build_enhanced_system_prompt()
            
            print(f"✅ _build_enhanced_system_prompt成功!")
            print(f"📝 系统提示词长度: {len(system_prompt) if system_prompt else 0}")
            print(f"📝 系统提示词内容预览: {system_prompt[:200] if system_prompt else 'None'}...")
            
            # 检查是否返回None
            if system_prompt is None:
                print("❌ 系统提示词返回None")
                return False
            elif not isinstance(system_prompt, str):
                print(f"❌ 系统提示词返回类型错误: {type(system_prompt)}")
                return False
            elif len(system_prompt) == 0:
                print("❌ 系统提示词返回空字符串")
                return False
            else:
                print("✅ 系统提示词内容有效")
            
        except Exception as e:
            print(f"❌ _build_enhanced_system_prompt失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_build_system_prompt())
    sys.exit(0 if success else 1) 