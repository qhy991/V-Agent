#!/usr/bin/env python3
"""
简单测试SystemPromptBuilder
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_communication.system_prompt_builder import SystemPromptBuilder
from core.llm_communication.managers.client_manager import CallType
from core.schema_system.enums import AgentCapability

async def test_system_prompt_builder():
    """测试SystemPromptBuilder"""
    print("🔍 测试SystemPromptBuilder...")
    
    try:
        # 1. 创建SystemPromptBuilder
        print("📋 创建SystemPromptBuilder...")
        builder = SystemPromptBuilder()
        print("✅ SystemPromptBuilder创建成功")
        
        # 2. 测试协调器模板
        print("\n🤖 测试协调器模板...")
        capabilities = {
            AgentCapability.TASK_COORDINATION,
            AgentCapability.WORKFLOW_MANAGEMENT
        }
        
        system_prompt = await builder.build_system_prompt(
            role="coordinator",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_coordinator",
            capabilities=capabilities,
            metadata={"has_tools": True, "tools_count": 5}
        )
        
        print(f"✅ 协调器模板生成成功")
        print(f"📝 模板长度: {len(system_prompt)}")
        print(f"📝 模板内容预览: {system_prompt[:200]}...")
        
        # 3. 检查是否返回None
        if system_prompt is None:
            print("❌ 模板返回None")
            return False
        elif not isinstance(system_prompt, str):
            print(f"❌ 模板返回类型错误: {type(system_prompt)}")
            return False
        elif len(system_prompt) == 0:
            print("❌ 模板返回空字符串")
            return False
        else:
            print("✅ 模板内容有效")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_system_prompt_builder())
    sys.exit(0 if success else 1) 