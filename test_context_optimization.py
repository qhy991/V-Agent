#!/usr/bin/env python3
"""
测试上下文传递优化
Test Context Optimization
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_tdd_test import UnifiedTDDTest


async def test_context_optimization():
    """测试上下文优化功能"""
    print("🧪 开始测试上下文优化TDD框架")
    
    try:
        # 创建实验实例
        experiment = UnifiedTDDTest(
            design_type="alu",
            config_profile="standard",
            custom_config={"max_iterations": 2}  # 限制迭代次数用于测试
        )
        
        print("✅ 实验实例创建成功")
        
        # 运行实验
        result = await experiment.run_experiment()
        
        # 分析结果
        print("📊 分析实验结果")
        print(f"✅ 执行成功: {result.get('success', False)}")
        print(f"🔄 总迭代次数: {result.get('total_iterations', 0)}")
        print(f"📁 上下文文件数: {len(experiment.context_state['generated_files'])}")
        
        # 显示上下文状态
        print("\n📋 上下文状态详情:")
        for i, file_info in enumerate(experiment.context_state['generated_files'], 1):
            print(f"  文件 {i}:")
            print(f"    - 文件名: {file_info.get('filename', 'unknown')}")
            print(f"    - 路径: {file_info.get('filepath', 'unknown')}")
            print(f"    - 类型: {file_info.get('file_type', 'unknown')}")
            print(f"    - 描述: {file_info.get('description', '无')}")
            print(f"    - 分类: {file_info.get('category', 'unknown')}")
            print()
        
        # 测试动态任务描述生成
        print("🧪 测试动态任务描述生成:")
        design_task = experiment.create_dynamic_task_description("设计ALU", "design")
        test_task = experiment.create_dynamic_task_description("测试ALU", "test")
        
        print("设计阶段任务描述:")
        print(design_task[:200] + "..." if len(design_task) > 200 else design_task)
        print("\n测试阶段任务描述:")
        print(test_task[:200] + "..." if len(test_task) > 200 else test_task)
        
        return result["success"]
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_context_optimization())
    print(f"\n🏁 测试结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1) 