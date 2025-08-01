#!/usr/bin/env python3
"""
多智能体架构演示测试套件
Multi-Agent Architecture Demo Test Suite

快速演示你的多智能体框架的核心能力：
1. 协调器智能选择和调度
2. 复杂工具调用链执行
3. 智能错误处理和修复
4. 完整的RISC-V项目协作
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))


async def run_quick_demo():
    """运行快速演示"""
    print("🎭 多智能体架构快速演示")
    print("="*60)
    print("本演示将展示:")
    print("✅ 中心化协调器的智能任务分配")
    print("✅ 多智能体的无缝协作")
    print("✅ 复杂工具调用链的执行")
    print("✅ 智能错误处理和修复")
    print("✅ 文件传递和数据协作")
    print()
    
    total_start_time = time.time()
    
    try:
        # 演示1: 协调器智能选择 (快速版)
        print("🧠 演示1: 协调器智能选择与调度")
        print("-" * 40)
        
        from test_coordinator_agent_selection import test_coordinator_intelligence
        demo1_start = time.time()
        
        # 运行简化的协调器测试
        coordinator_result = await test_coordinator_intelligence()
        demo1_time = time.time() - demo1_start
        
        print(f"✅ 协调器演示完成 ({demo1_time:.1f}秒)")
        print(f"🤝 协作能力评分: {coordinator_result['collaboration_score']:.1f}%")
        print(f"📁 生成文件: {coordinator_result['files_generated']}个")
        
    except Exception as e:
        print(f"❌ 协调器演示失败: {str(e)}")
        coordinator_result = {"collaboration_score": 0, "files_generated": 0}
    
    print()
    
    try:
        # 演示2: 高级工具交互 (选择性执行)
        print("🔧 演示2: 高级工具交互与错误处理")
        print("-" * 40)
        
        from test_advanced_tool_interaction import test_complex_tool_chain, test_error_injection_recovery
        demo2_start = time.time()
        
        # 只运行关键的工具链测试
        print("🔗 执行复杂工具调用链...")
        chain_result = await test_complex_tool_chain()
        
        print("🚨 执行错误注入与恢复测试...")
        error_result = await test_error_injection_recovery()
        
        demo2_time = time.time() - demo2_start
        
        print(f"✅ 工具交互演示完成 ({demo2_time:.1f}秒)")
        print(f"🔧 工具调用次数: {chain_result['tool_calls']}")
        print(f"🚨 错误恢复率: {error_result['recovery_rate']:.1f}%") 
        
    except Exception as e:
        print(f"❌ 工具交互演示失败: {str(e)}")
        chain_result = {"tool_calls": 0}
        error_result = {"recovery_rate": 0}
    
    print()
    
    # 综合评估
    total_time = time.time() - total_start_time
    
    print("📊 演示总结")
    print("="*60)
    print(f"⏱️ 总演示时间: {total_time:.1f}秒")
    print(f"🤝 协作能力: {coordinator_result['collaboration_score']:.1f}%")
    print(f"🔧 工具调用能力: {chain_result['tool_calls']} 次调用")
    print(f"🚨 错误处理能力: {error_result['recovery_rate']:.1f}% 恢复率")
    print(f"📁 文件生成能力: {coordinator_result['files_generated']} 个文件")
    
    # 总体评分
    overall_score = (
        coordinator_result['collaboration_score'] * 0.4 +
        min(chain_result['tool_calls'] * 10, 100) * 0.3 +
        error_result['recovery_rate'] * 0.3
    )
    
    print(f"\n🏆 架构综合评分: {overall_score:.1f}/100")
    
    if overall_score >= 80:
        print("🌟 评级: 优秀 - 多智能体架构表现卓越！")
        print("   ✨ 协调器智能程度高")
        print("   ✨ 工具调用链流畅")
        print("   ✨ 错误处理能力强")
    elif overall_score >= 60:
        print("🔶 评级: 良好 - 架构基础扎实，有优化空间")
        print("   💡 建议进一步优化协调机制")
        print("   💡 可以增强错误处理逻辑")
    else:
        print("❌ 评级: 需要改进 - 核心功能存在问题")
        print("   🔧 需要检查协调器逻辑")
        print("   🔧 需要完善工具调用机制")
    
    return overall_score >= 60


async def run_comprehensive_test():
    """运行完整的综合测试"""
    print("\n🚀 是否运行完整的RISC-V项目测试？")
    print("这将展示最复杂的多智能体协作场景 (预计需要5-10分钟)")
    
    # 为了演示，我们默认跳过最耗时的测试
    user_choice = input("输入 'y' 运行完整测试，或按回车跳过: ").strip().lower()
    
    if user_choice == 'y':
        print("\n🏗️ 启动完整RISC-V项目测试...")
        try:
            from test_multi_agent_riscv_project import MultiAgentRISCVTest
            
            tester = MultiAgentRISCVTest()
            comprehensive_result = await tester.run_comprehensive_test()
            
            print("✅ 完整项目测试成功完成！")
            return True
        except Exception as e:
            print(f"❌ 完整项目测试失败: {str(e)}")
            return False
    else:
        print("⏭️ 跳过完整项目测试")
        return True


def print_usage_guide():
    """打印使用指南"""
    print(f"\n📖 测试文件使用指南")
    print("="*60)
    print("本目录包含以下测试文件:")
    print()
    print("1️⃣ test_coordinator_agent_selection.py")
    print("   🎯 测试协调器的智能选择和调度能力")
    print("   ⚡ 快速测试 (约2-3分钟)")
    print("   📋 命令: python test_coordinator_agent_selection.py")
    print()
    print("2️⃣ test_advanced_tool_interaction.py")
    print("   🔧 测试复杂工具调用链和错误处理")
    print("   ⚡ 中等耗时 (约3-5分钟)")
    print("   📋 命令: python test_advanced_tool_interaction.py")
    print()
    print("3️⃣ test_multi_agent_riscv_project.py")
    print("   🏗️ 完整的RISC-V项目多智能体协作")
    print("   ⚡ 耗时较长 (约5-10分钟)")
    print("   📋 命令: python test_multi_agent_riscv_project.py")
    print()
    print("4️⃣ run_demo_tests.py (当前文件)")
    print("   🎭 快速演示所有核心功能")
    print("   ⚡ 综合演示 (约3-5分钟)")
    print("   📋 命令: python run_demo_tests.py")
    print()
    print("💡 建议运行顺序:")
    print("   1. 先运行 run_demo_tests.py 了解整体能力")
    print("   2. 根据兴趣运行特定的专项测试")
    print("   3. 最后运行完整的RISC-V项目测试")


async def main():
    """主函数"""
    print("🚀 多智能体架构演示测试套件")
    print("="*60)
    
    try:
        # 运行快速演示
        demo_success = await run_quick_demo()
        
        if demo_success:
            # 询问是否运行完整测试
            await run_comprehensive_test()
        
        # 显示使用指南
        print_usage_guide()
        
        print(f"\n🎉 演示完成！")
        print(f"📂 查看生成的文件和日志以了解详细执行过程")
        
        return demo_success
        
    except KeyboardInterrupt:
        print("\n⚠️ 演示被用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 演示执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)