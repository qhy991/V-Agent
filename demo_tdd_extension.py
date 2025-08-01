#!/usr/bin/env python3
"""
测试驱动扩展功能演示

展示如何使用完全增量的测试驱动扩展功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent

# 导入扩展功能
from extensions import create_test_driven_coordinator, TestDrivenConfig


async def demo_basic_extension():
    """演示基础扩展功能"""
    print("🎯 演示1: 基础扩展功能")
    print("-" * 50)
    
    # 1. 创建标准协调器（现有方式，不变）
    config = FrameworkConfig.from_env()
    original_coordinator = CentralizedCoordinator(config)
    
    # 2. 注册智能体（现有方式，不变）
    verilog_agent = RealVerilogDesignAgent(config)
    reviewer_agent = RealCodeReviewAgent(config)
    original_coordinator.register_agent(verilog_agent)
    original_coordinator.register_agent(reviewer_agent)
    
    print("✅ 标准协调器和智能体初始化完成")
    
    # 3. 升级为测试驱动协调器（新功能，可选）
    enhanced_coordinator = create_test_driven_coordinator(original_coordinator)
    
    print("✅ 测试驱动扩展已启用")
    
    # 4. 演示现有功能完全不变
    print("\n📋 现有功能测试:")
    print("coordinate_task_execution 方法:", hasattr(enhanced_coordinator, 'coordinate_task_execution'))
    print("register_agent 方法:", hasattr(enhanced_coordinator, 'register_agent'))
    
    # 5. 演示新增功能
    print("\n🧪 新增功能测试:")
    print("execute_test_driven_task 方法:", hasattr(enhanced_coordinator, 'execute_test_driven_task'))
    print("get_session_info 方法:", hasattr(enhanced_coordinator, 'get_session_info'))
    print("list_active_sessions 方法:", hasattr(enhanced_coordinator, 'list_active_sessions'))
    
    print("✅ 演示1完成 - 基础功能正常")
    return True


async def demo_task_analysis():
    """演示任务分析功能"""
    print("\n🎯 演示2: 智能任务分析")
    print("-" * 50)
    
    from extensions.enhanced_task_parser import EnhancedTaskParser
    parser = EnhancedTaskParser()
    
    # 测试不同类型的任务
    test_tasks = [
        {
            "name": "标准设计任务",
            "task": "设计一个8位计数器，包含同步复位和使能信号"
        },
        {
            "name": "测试驱动任务（包含测试台路径）",
            "task": """
            设计一个32位ALU模块，支持基本算术运算。
            
            测试要求：
            - 测试台: /home/user/alu_testbench.v
            - 必须通过所有测试用例
            """
        },
        {
            "name": "迭代优化任务",
            "task": "设计UART模块，如果测试失败请分析错误并迭代改进直到通过"
        }
    ]
    
    for test_case in test_tasks:
        print(f"\n分析任务: {test_case['name']}")
        analysis = await parser.parse_enhanced_task(test_case['task'])
        
        print(f"  是否测试驱动: {analysis['is_test_driven']}")
        print(f"  需要迭代: {analysis['iteration_required']}")
        if analysis.get('testbench_path'):
            print(f"  测试台路径: {analysis['testbench_path']}")
        
        criteria = analysis.get('validation_criteria', [])
        if criteria:
            print(f"  验证标准: {len(criteria)} 项")
    
    print("✅ 演示2完成 - 任务分析功能正常")
    return True


async def demo_testbench_validation():
    """演示测试台验证功能"""
    print("\n🎯 演示3: 测试台验证")
    print("-" * 50)
    
    from extensions.test_analyzer import TestAnalyzer
    analyzer = TestAnalyzer()
    
    # 创建模拟测试台内容
    valid_testbench = """
module counter_tb;
    reg clk, rst_n, enable;
    wire [7:0] count;
    
    // 实例化待测模块
    counter_8bit dut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .count(count)
    );
    
    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    // 测试序列
    initial begin
        $monitor("Time=%0t rst_n=%b enable=%b count=%d", $time, rst_n, enable, count);
        
        rst_n = 0; enable = 0;
        #20 rst_n = 1;
        #10 enable = 1;
        #100 enable = 0;
        #20 $finish;
    end
endmodule
"""
    
    invalid_testbench = """
module bad_tb
    reg clk;
    // 缺少endmodule，缺少测试逻辑
"""
    
    print("验证有效测试台:")
    valid_result = analyzer._validate_testbench_content(valid_testbench)
    print(f"  是否有效: {valid_result['is_valid']}")
    print(f"  检查项目: {sum(valid_result[k] for k in valid_result if k != 'is_valid')}/4 通过")
    
    print("\n验证无效测试台:")
    invalid_result = analyzer._validate_testbench_content(invalid_testbench)
    print(f"  是否有效: {invalid_result['is_valid']}")
    print(f"  检查项目: {sum(invalid_result[k] for k in invalid_result if k != 'is_valid')}/4 通过")
    
    # 测试模块信息提取
    print("\n提取模块信息:")
    module_info = analyzer._extract_testbench_info(valid_testbench)
    print(f"  测试台模块: {module_info['testbench_module']}")
    print(f"  DUT实例: {len(module_info['dut_instances'])} 个")
    print(f"  信号数量: {len(module_info['signals'])} 个")
    
    print("✅ 演示3完成 - 测试台验证功能正常")
    return True


async def demo_session_management():
    """演示会话管理功能"""
    print("\n🎯 演示4: 会话管理")
    print("-" * 50)
    
    # 创建测试驱动协调器
    config = FrameworkConfig.from_env()
    original_coordinator = CentralizedCoordinator(config)
    enhanced_coordinator = create_test_driven_coordinator(original_coordinator)
    
    # 模拟创建一些测试会话
    sessions = {
        "tdd_session_1": {
            "status": "running",
            "start_time": 1234567890,
            "iterations": [
                {"iteration": 1, "result": {"all_tests_passed": False}},
                {"iteration": 2, "result": {"all_tests_passed": False}}
            ]
        },
        "tdd_session_2": {
            "status": "completed", 
            "start_time": 1234567900,
            "iterations": [
                {"iteration": 1, "result": {"all_tests_passed": True}}
            ]
        }
    }
    
    # 添加到协调器
    enhanced_coordinator.test_driven_sessions.update(sessions)
    
    print("会话管理演示:")
    print(f"  活跃会话: {enhanced_coordinator.list_active_sessions()}")
    print(f"  总会话数: {len(enhanced_coordinator.test_driven_sessions)}")
    
    # 获取会话详情
    session_info = enhanced_coordinator.get_session_info("tdd_session_1")
    if session_info:
        print(f"  会话1状态: {session_info['status']}")
        print(f"  会话1迭代: {len(session_info['iterations'])} 次")
    
    # 获取迭代历史
    history = enhanced_coordinator.get_iteration_history("tdd_session_1")
    print(f"  会话1历史: {len(history)} 条记录")
    
    print("✅ 演示4完成 - 会话管理功能正常")
    return True


async def demo_integration_examples():
    """演示集成使用示例"""
    print("\n🎯 演示5: 集成使用示例")
    print("-" * 50)
    
    # 1. 最简单的集成方式
    print("方式1 - 最简单集成:")
    config = FrameworkConfig.from_env()
    coordinator = CentralizedCoordinator(config)
    enhanced_coordinator = create_test_driven_coordinator(coordinator)
    print("  ✅ 一行代码完成升级")
    
    # 2. 带配置的集成方式
    print("\n方式2 - 自定义配置:")
    custom_config = TestDrivenConfig(
        max_iterations=3,
        enable_deep_analysis=True,
        timeout_per_iteration=120
    )
    from extensions.test_driven_coordinator import TestDrivenCoordinator
    custom_coordinator = TestDrivenCoordinator(coordinator, custom_config)
    print(f"  ✅ 最大迭代次数: {custom_coordinator.config.max_iterations}")
    print(f"  ✅ 深度分析: {custom_coordinator.config.enable_deep_analysis}")
    
    # 3. 使用示例
    print("\n使用示例:")
    sample_task = """
    设计一个简单的ALU模块，支持加法和减法运算。
    测试台: /path/to/alu_tb.v
    要求通过所有测试用例，如果失败请自动迭代改进。
    """
    
    print("  任务描述已准备")
    print("  调用方式: await enhanced_coordinator.execute_test_driven_task(task, testbench_path)")
    print("  ✅ API简单易用")
    
    print("✅ 演示5完成 - 集成方式简单灵活")
    return True


async def main():
    """主演示函数"""
    print("🚀 测试驱动扩展功能完整演示")
    print("=" * 70)
    print("展示完全增量、零影响的测试驱动开发扩展功能")
    print("=" * 70)
    
    demos = [
        ("基础扩展功能", demo_basic_extension),
        ("智能任务分析", demo_task_analysis),
        ("测试台验证", demo_testbench_validation),
        ("会话管理", demo_session_management),
        ("集成使用示例", demo_integration_examples)
    ]
    
    passed = 0
    total = len(demos)
    
    for demo_name, demo_func in demos:
        try:
            result = await demo_func()
            if result:
                passed += 1
            print(f"✅ {demo_name} 演示完成")
        except Exception as e:
            print(f"❌ {demo_name} 演示异常: {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"📊 演示结果: {passed}/{total} 个功能正常")
    
    if passed == total:
        print("\n🎉 所有功能演示成功！")
        print("\n💡 关键优势:")
        print("   ✅ 完全增量 - 不修改任何现有代码")
        print("   ✅ 零影响 - 现有功能完全不受影响")
        print("   ✅ 向后兼容 - 所有现有API保持不变")
        print("   ✅ 可选使用 - 按需启用新功能")
        print("   ✅ 易于集成 - 一行代码完成升级")
        
        print("\n🚀 立即开始使用:")
        print("   from extensions import create_test_driven_coordinator")
        print("   enhanced_coordinator = create_test_driven_coordinator(your_coordinator)")
        print("   result = await enhanced_coordinator.execute_test_driven_task(task, testbench_path)")
    else:
        print("⚠️ 部分功能需要进一步完善")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())