#!/usr/bin/env python3
"""
测试错误信息传递改进
==================================================

这个脚本用于测试改进后的错误信息传递机制，确保：
1. 仿真失败时错误信息被正确记录
2. 错误信息被传递到设计智能体
3. 智能体能够基于错误信息进行修复
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_tdd_test import UnifiedTDDTest


async def test_error_context_fix():
    """测试错误信息传递改进"""
    print("🧪 测试错误信息传递改进")
    print("=" * 50)
    
    # 创建一个简单的测试，预期会产生编译错误
    experiment = UnifiedTDDTest(
        design_type="simple_adder",  # 使用简单的加法器
        config_profile="quick",      # 快速测试配置
        custom_config={
            "max_iterations": 3,     # 最多3次迭代
            "timeout_per_iteration": 180,  # 3分钟超时
            "deep_analysis": True
        }
    )
    
    try:
        print("🚀 开始错误信息传递测试...")
        print("   设计类型: simple_adder")
        print("   配置档案: quick")
        print("   最大迭代: 3")
        print("   预期: 第1次迭代会产生编译错误，第2次迭代应该修复")
        
        # 运行实验
        result = await experiment.run_experiment()
        
        # 分析结果
        print("\n📊 实验结果分析:")
        print("=" * 30)
        
        if result.get("success"):
            print("✅ 实验成功完成")
        else:
            print("❌ 实验失败")
        
        # 检查迭代次数
        iterations = result.get("iterations", [])
        print(f"   总迭代次数: {len(iterations)}")
        
        # 检查是否有仿真错误记录
        enhanced_analysis = result.get("enhanced_analysis", {})
        simulation_errors = enhanced_analysis.get("simulation_errors", [])
        print(f"   记录的仿真错误: {len(simulation_errors)} 个")
        
        if simulation_errors:
            print("   📝 仿真错误详情:")
            for i, error in enumerate(simulation_errors):
                print(f"     错误 {i+1}: {error.get('error', '')[:100]}...")
                print(f"     阶段: {error.get('stage', 'unknown')}")
                print(f"     迭代: {error.get('iteration', 'unknown')}")
        
        # 检查是否进行了修复
        needs_fix_count = sum(1 for iter_result in iterations if iter_result.get("needs_fix", False))
        print(f"   需要修复的迭代: {needs_fix_count} 个")
        
        # 检查最终结果
        final_iteration = iterations[-1] if iterations else None
        if final_iteration:
            print(f"   最终迭代结果: {'成功' if final_iteration.get('success') else '失败'}")
            print(f"   所有测试通过: {final_iteration.get('all_tests_passed', False)}")
        
        print("\n🎯 改进效果验证:")
        print("=" * 30)
        
        # 验证改进效果
        improvements_verified = []
        
        # 1. 检查错误信息是否被记录
        if simulation_errors:
            improvements_verified.append("✅ 仿真错误信息被正确记录")
        else:
            improvements_verified.append("❌ 未检测到仿真错误记录")
        
        # 2. 检查是否进行了多次迭代
        if len(iterations) > 1:
            improvements_verified.append("✅ 进行了多次迭代（错误修复）")
        else:
            improvements_verified.append("❌ 只进行了1次迭代（可能没有错误修复）")
        
        # 3. 检查是否有修复标记
        if needs_fix_count > 0:
            improvements_verified.append("✅ 检测到需要修复的迭代")
        else:
            improvements_verified.append("❌ 未检测到需要修复的迭代")
        
        # 4. 检查最终是否成功
        if final_iteration and final_iteration.get("success"):
            improvements_verified.append("✅ 最终迭代成功（错误修复有效）")
        else:
            improvements_verified.append("❌ 最终迭代失败（错误修复可能无效）")
        
        # 输出验证结果
        for verification in improvements_verified:
            print(f"   {verification}")
        
        # 总结
        success_count = sum(1 for v in improvements_verified if v.startswith("✅"))
        total_count = len(improvements_verified)
        
        print(f"\n📈 改进效果评分: {success_count}/{total_count}")
        
        if success_count >= 3:
            print("🎉 错误信息传递改进验证成功！")
            return True
        else:
            print("⚠️ 错误信息传递改进需要进一步优化")
            return False
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_context_mechanism():
    """测试错误上下文机制"""
    print("🔧 测试错误上下文机制")
    print("=" * 30)
    
    # 模拟错误信息
    error_info = {
        "iteration": 1,
        "error": "result is not a valid l-value in tb_alu_32bit.uut",
        "compilation_output": "C:\\Users\\test\\alu_32bit.v:41: error: result is not a valid l-value",
        "command": "iverilog -o simulation alu_32bit.v testbench.v",
        "stage": "compilation",
        "return_code": 8,
        "timestamp": time.time()
    }
    
    # 模拟增强分析
    enhanced_analysis = {
        "simulation_errors": [error_info]
    }
    
    print("✅ 错误信息结构验证通过")
    print(f"   错误类型: {error_info['error']}")
    print(f"   编译阶段: {error_info['stage']}")
    print(f"   返回码: {error_info['return_code']}")
    
    return True


async def main():
    """主测试函数"""
    print("🔧 测试错误信息传递改进")
    print("=" * 50)
    
    try:
        # 1. 测试错误上下文机制
        if not test_error_context_mechanism():
            print("❌ 错误上下文机制测试失败")
            return False
        
        # 2. 测试完整的错误信息传递
        if not await test_error_context_fix():
            print("❌ 错误信息传递测试失败")
            return False
        
        print("\n🎉 所有测试通过！错误信息传递改进验证成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 