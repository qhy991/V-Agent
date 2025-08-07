#!/usr/bin/env python3
"""
测试系统提示词修复效果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 直接导入SystemPromptBuilder
from core.llm_communication.system_prompt_builder import SystemPromptBuilder
from core.llm_communication.managers.client_manager import CallType
from core.schema_system.enums import AgentCapability


async def test_system_prompt_fix():
    """测试系统提示词修复效果"""
    print("🧪 测试系统提示词修复效果")
    print("=" * 50)
    
    try:
        # 创建SystemPromptBuilder
        prompt_builder = SystemPromptBuilder()
        print("✅ SystemPromptBuilder创建成功")
        
        # 构建协调器的系统提示词
        system_prompt = await prompt_builder.build_system_prompt(
            role="coordinator",
            call_type=CallType.FUNCTION_CALLING,
            agent_id="test_coordinator",
            capabilities={
                AgentCapability.TASK_COORDINATION,
                AgentCapability.WORKFLOW_MANAGEMENT,
                AgentCapability.SPECIFICATION_ANALYSIS
            },
            metadata={
                "has_tools": True,
                "tools_count": 5
            }
        )
        
        print(f"✅ 系统提示词构建成功")
        print(f"长度: {len(system_prompt)} 字符")
        
        # 检查关键内容
        checks = {
            "禁止直接回答": "禁止直接回答" in system_prompt,
            "identify_task_type": "identify_task_type" in system_prompt,
            "JSON格式": "JSON格式" in system_prompt,
            "工具调用": "工具调用" in system_prompt,
            "强制Function Calling": "强制Function Calling" in system_prompt,
            "必须调用工具": "必须调用工具" in system_prompt
        }
        
        print("\n📊 内容检查结果:")
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {result}")
        
        # 显示提示词的关键部分
        print(f"\n📝 系统提示词关键部分:")
        
        # 查找关键段落
        key_sections = [
            "🚨 **强制Function Calling模式**",
            "⚠️ **重要规则**",
            "🎯 **协调器特殊要求**",
            "❌ **禁止行为**",
            "✅ **正确行为**"
        ]
        
        for section in key_sections:
            if section in system_prompt:
                start_idx = system_prompt.find(section)
                end_idx = system_prompt.find("\n\n", start_idx)
                if end_idx == -1:
                    end_idx = start_idx + 200
                
                section_content = system_prompt[start_idx:end_idx]
                print(f"\n{section}:")
                print(section_content)
        
        # 总体评估
        success_count = sum(checks.values())
        total_count = len(checks)
        
        print(f"\n📈 总体评估:")
        print(f"成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count >= total_count * 0.8:
            print("✅ 系统提示词修复成功！")
        else:
            print("❌ 系统提示词修复不完整")
        
        return system_prompt
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """主测试函数"""
    print("🚀 开始系统提示词修复验证测试")
    print("=" * 60)
    
    await test_system_prompt_fix()
    
    print("\n🎉 测试完成")


if __name__ == "__main__":
    asyncio.run(main()) 