#!/usr/bin/env python3
"""
测试None响应修复效果
"""

import asyncio
import logging
from core.llm_coordinator_agent import LLMCoordinatorAgent
from config.config import FrameworkConfig

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_none_response_fix():
    """测试None响应修复效果"""
    print("🔧 测试None响应修复效果...")
    
    try:
        # 加载配置
        config = FrameworkConfig.from_env()
        
        # 创建协调器
        coordinator = LLMCoordinatorAgent(config)
        
        # 测试任务
        test_request = """请设计一个名为 counter 的Verilog模块。

**基本要求**：
1. 生成完整、可编译的Verilog代码
2. 包含适当的端口定义和功能实现
3. 符合Verilog标准语法
4. 生成对应的测试台进行验证

**质量要求**：
- 代码结构清晰，注释完善
- 遵循良好的命名规范
- 确保功能正确性"""
        
        print("🚀 开始执行协调任务...")
        
        # 执行协调任务
        result = await coordinator.coordinate_task(
            user_request=test_request,
            max_iterations=4,
        )
        
        print("✅ 协调任务执行完成!")
        print("=" * 60)
        print("📋 执行结果:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print("=" * 60)
        
        # 检查是否还有None响应错误
        if "object of type 'NoneType' has no len()" in str(result):
            print("❌ 仍然存在None响应错误")
            return False
        else:
            print("✅ None响应错误已修复")
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_none_response_fix())
    if success:
        print("🎉 None响应修复验证成功!")
    else:
        print("💥 None响应修复验证失败!") 