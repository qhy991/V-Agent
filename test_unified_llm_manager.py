#!/usr/bin/env python3
"""
直接测试UnifiedLLMClientManager
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.llm_communication.managers.client_manager import UnifiedLLMClientManager
from core.llm_communication.system_prompt_builder import SystemPromptBuilder
from core.llm_communication.managers.client_manager import CallType
from core.schema_system.enums import AgentCapability

async def test_unified_llm_manager():
    """直接测试UnifiedLLMClientManager"""
    print("🔍 直接测试UnifiedLLMClientManager...")
    
    try:
        # 1. 加载配置
        print("📋 加载配置...")
        config = FrameworkConfig.from_env()
        print(f"✅ 配置加载成功")
        
        # 2. 创建UnifiedLLMClientManager
        print("\n🔧 创建UnifiedLLMClientManager...")
        llm_manager = UnifiedLLMClientManager(
            agent_id="test_coordinator",
            role="coordinator",
            config=config
        )
        print("✅ UnifiedLLMClientManager创建成功")
        
        # 3. 创建SystemPromptBuilder
        print("\n📝 创建SystemPromptBuilder...")
        prompt_builder = SystemPromptBuilder()
        print("✅ SystemPromptBuilder创建成功")
        
        # 4. 创建测试对话
        print("\n💬 创建测试对话...")
        conversation = [
            {
                "role": "user",
                "content": "请帮我设计一个4位加法器"
            }
        ]
        print(f"✅ 测试对话创建成功，长度: {len(conversation)}")
        
        # 5. 测试Function Calling调用
        print("\n🚀 测试Function Calling调用...")
        try:
            response = await llm_manager.call_llm_for_function_calling(
                conversation=conversation,
                system_prompt_builder=lambda: prompt_builder.build_system_prompt(
                    role="coordinator",
                    call_type=CallType.FUNCTION_CALLING,
                    agent_id="test_coordinator",
                    capabilities={
                        AgentCapability.TASK_COORDINATION,
                        AgentCapability.WORKFLOW_MANAGEMENT
                    },
                    metadata={"has_tools": True, "tools_count": 5}
                )
            )
            
            print(f"✅ Function Calling调用成功!")
            print(f"📝 响应长度: {len(response) if response else 0}")
            print(f"📝 响应内容预览: {response[:200] if response else 'None'}...")
            
        except Exception as e:
            print(f"❌ Function Calling调用失败: {str(e)}")
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
    success = asyncio.run(test_unified_llm_manager())
    sys.exit(0 if success else 1) 