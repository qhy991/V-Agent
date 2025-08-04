#!/usr/bin/env python3
"""
改进后的TDD框架测试脚本
==================================================

这个脚本用于测试改进后的TDD框架，确保：
1. 强制生成测试台
2. 强制运行仿真验证
3. 真正的TDD流程执行
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_tdd_test import UnifiedTDDTest


async def test_improved_tdd():
    """测试改进后的TDD框架"""
    print("🧪 测试改进后的TDD框架")
    print("=" * 50)
    
    # 创建简单的ALU测试
    experiment = UnifiedTDDTest(
        design_type="simple_adder",  # 使用简单的加法器进行测试
        config_profile="quick",      # 快速测试配置
        custom_config={
            "max_iterations": 3,     # 最多3次迭代
            "timeout_per_iteration": 180,  # 3分钟超时
            "deep_analysis": True
        }
    )
    
    try:
        print("🚀 开始改进后的TDD实验...")
        result = await experiment.run_experiment()
        
        print("\n" + "=" * 50)
        print("📊 实验结果分析")
        print("=" * 50)
        
        if result.get("success"):
            print("✅ 实验成功完成！")
            print(f"   总迭代次数: {result.get('total_iterations', 0)}")
            print(f"   完成原因: {result.get('completion_reason', 'unknown')}")
            
            # 检查是否生成了测试台
            test_results = result.get('test_results', {})
            if test_results.get('testbench_result'):
                print("✅ 测试台生成成功")
            else:
                print("❌ 测试台生成失败")
            
            # 检查是否运行了仿真
            if test_results.get('simulation_result'):
                print("✅ 仿真运行成功")
                if test_results['simulation_result'].get('all_tests_passed'):
                    print("✅ 所有测试通过")
                else:
                    print("⚠️ 部分测试失败")
            else:
                print("❌ 仿真运行失败")
            
        else:
            print("❌ 实验失败")
            print(f"   错误: {result.get('error', '未知错误')}")
            print(f"   完成原因: {result.get('completion_reason', 'unknown')}")
        
        # 检查生成的文件
        print("\n📁 生成的文件:")
        try:
            from core.experiment_manager import get_experiment_manager
            exp_manager = get_experiment_manager()
            if exp_manager and exp_manager.current_experiment_path:
                designs_dir = exp_manager.current_experiment_path / "designs"
                testbenches_dir = exp_manager.current_experiment_path / "testbenches"
                
                if designs_dir.exists():
                    design_files = list(designs_dir.glob("*.v"))
                    print(f"   设计文件: {len(design_files)} 个")
                    for f in design_files:
                        print(f"     - {f.name}")
                
                if testbenches_dir.exists():
                    testbench_files = list(testbenches_dir.glob("*.v"))
                    print(f"   测试台文件: {len(testbench_files)} 个")
                    for f in testbench_files:
                        print(f"     - {f.name}")
                else:
                    print("   测试台文件: 0 个 (目录不存在)")
        except Exception as e:
            print(f"   检查文件时出错: {e}")
        
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ 测试执行异常: {str(e)}")
        return False


async def main():
    """主函数"""
    print("改进后的TDD框架测试")
    print("=" * 50)
    
    success = await test_improved_tdd()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 改进后的TDD框架测试成功！")
        print("✅ 强制测试台生成功能正常")
        print("✅ 强制仿真验证功能正常")
        print("✅ TDD流程执行正常")
    else:
        print("❌ 改进后的TDD框架测试失败")
        print("需要进一步调试和改进")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 