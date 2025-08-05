#!/usr/bin/env python3
"""
测试system prompt修复的脚本
验证LLM协调智能体是否正确传递system prompt并返回工具调用格式
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig
from core.enhanced_logging_config import setup_enhanced_logging

async def test_system_prompt_fix():
    """测试system prompt修复"""
    print("🧪 开始测试system prompt修复...")
    
    # 设置日志
    setup_enhanced_logging()
    
    # 加载配置
    config = FrameworkConfig.from_env()
    
    # 创建协调智能体
    coordinator = LLMCoordinatorAgent(config)
    
    # 创建测试智能体
    verilog_agent = EnhancedRealVerilogAgent(config)
    review_agent = EnhancedRealCodeReviewAgent(config)
    
    # 注册智能体
    await coordinator.register_agent(verilog_agent)
    await coordinator.register_agent(review_agent)
    
    # 测试用户请求
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
    
    print(f"📝 测试请求: {test_request.strip()}")
    print("=" * 80)
    
    try:
        # 执行协调任务
        result = await coordinator.coordinate_task(
            user_request=test_request,
            conversation_id="test_system_prompt_fix",
            max_iterations=3
        )
        
        print("✅ 测试完成!")
        print(f"📊 结果: {result.get('success', False)}")
        print(f"📄 协调结果: {result.get('coordination_result', '')[:500]}...")
        
        # 检查是否返回了工具调用格式
        coordination_result = result.get('coordination_result', '')
        if 'tool_calls' in coordination_result or 'identify_task_type' in coordination_result:
            print("✅ System prompt修复成功 - 返回了工具调用格式")
        else:
            print("❌ System prompt修复失败 - 仍然返回了描述性文本")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_system_prompt_fix()) 