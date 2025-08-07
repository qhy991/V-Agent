#!/usr/bin/env python3
"""
测试LLM协调智能体修复效果
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
from agents.enhanced_real_code_review_agent import EnhancedRealCodeReviewAgentRefactored
from config.config import FrameworkConfig


async def test_coordinator_fix():
    """测试协调智能体修复效果"""
    print("🧪 测试LLM协调智能体修复效果")
    print("=" * 50)
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        print("✅ 协调智能体创建成功")
        
        # 创建Verilog设计智能体
        verilog_agent = EnhancedRealVerilogAgentRefactored(config)
        print("✅ Verilog设计智能体创建成功")
        
        # 创建代码审查智能体
        review_agent = EnhancedRealCodeReviewAgentRefactored(config)
        print("✅ 代码审查智能体创建成功")
        
        # 注册智能体
        await coordinator.register_agent(verilog_agent)
        await coordinator.register_agent(review_agent)
        print("✅ 智能体注册成功")
        
        # 测试任务
        test_request = """
请设计一个名为 counter 的Verilog模块。

**基本要求**：
1. 生成完整、可编译的Verilog代码
2. 包含适当的端口定义和功能实现
3. 符合Verilog标准语法
4. 生成对应的测试台进行验证

**质量要求**：
- 代码结构清晰，注释完善
- 遵循良好的命名规范
- 确保功能正确性
"""
        
        print(f"\n📋 测试任务: {test_request[:100]}...")
        
        # 执行协调任务
        result = await coordinator.coordinate_task(
            user_request=test_request,
            max_iterations=5
        )
        
        print("\n📊 协调结果:")
        print(f"成功: {result.get('success', False)}")
        print(f"响应长度: {len(result.get('coordination_result', ''))}")
        print(f"智能体结果数量: {len(result.get('agent_results', {}))}")
        
        if result.get('success'):
            print("✅ 协调任务执行成功")
        else:
            print("❌ 协调任务执行失败")
            print(f"错误: {result.get('error', '未知错误')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_system_prompt():
    """测试系统提示词构建"""
    print("\n🧪 测试系统提示词构建")
    print("=" * 50)
    
    try:
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        
        # 构建系统提示词
        system_prompt = await coordinator._build_enhanced_system_prompt()
        
        print(f"✅ 系统提示词构建成功")
        print(f"长度: {len(system_prompt)} 字符")
        print(f"包含'禁止直接回答': {'禁止直接回答' in system_prompt}")
        print(f"包含'identify_task_type': {'identify_task_type' in system_prompt}")
        print(f"包含'JSON格式': {'JSON格式' in system_prompt}")
        
        # 显示提示词的前500字符
        print(f"\n📝 系统提示词预览:")
        print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
        
        return system_prompt
        
    except Exception as e:
        print(f"❌ 系统提示词测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """主测试函数"""
    print("🚀 开始LLM协调智能体修复验证测试")
    print("=" * 60)
    
    # 测试系统提示词
    await test_system_prompt()
    
    # 测试协调任务
    await test_coordinator_fix()
    
    print("\n🎉 测试完成")


if __name__ == "__main__":
    asyncio.run(main()) 