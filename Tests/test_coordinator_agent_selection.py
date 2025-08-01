#!/usr/bin/env python3
"""
协调器智能体选择和调度能力测试
Coordinator Agent Selection and Scheduling Test

专门测试中心化协调器的核心能力：
1. 智能分析任务并选择最适合的智能体
2. 智能体间的任务传递和协作
3. 工具调用链的协调执行
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging


async def test_coordinator_intelligence():
    """测试协调器的智能选择和调度能力"""
    print("🧠 协调器智能选择与调度测试")
    print("="*60)
    
    # 初始化
    config = FrameworkConfig.from_env()
    log_session = setup_enhanced_logging("coordinator_test")
    coordinator = CentralizedCoordinator(config)
    
    # 初始化智能体
    verilog_agent = RealVerilogDesignAgent(config)
    reviewer_agent = RealCodeReviewAgent(config)
    
    # 注册智能体到协调器
    coordinator.register_agent(verilog_agent)
    coordinator.register_agent(reviewer_agent)
    
    print(f"📂 工作目录: {log_session.get_artifacts_dir()}")
    print(f"🤖 已注册智能体: {len(coordinator.registered_agents)}个")
    
    # 测试场景1: 设计任务 - 应该选择Verilog设计智能体
    print(f"\n🎯 测试场景1: 设计任务智能分配")
    print("-" * 40)
    
    design_task = """
请设计一个8位二进制计数器模块，要求：
1. 支持同步复位
2. 包含使能信号
3. 输出当前计数值
4. 提供详细的端口说明

请生成完整的Verilog代码。
"""
    
    print("📋 任务类型: Verilog设计任务")
    print("🎯 期望选择: RealVerilogDesignAgent")
    
    start_time = time.time()
    result1 = await coordinator.coordinate_task_execution(design_task)
    time1 = time.time() - start_time
    
    print(f"⏱️ 执行时间: {time1:.2f}秒")
    # 处理协调器返回的字典格式
    result1_str = str(result1) if isinstance(result1, dict) else result1
    print(f"✅ 任务完成: {'成功' if len(result1_str) > 100 else '失败'}")
    
    # 测试场景2: 审查任务 - 应该选择代码审查智能体
    print(f"\n🔍 测试场景2: 审查任务智能分配")
    print("-" * 40)
    
    review_task = """
请对工件目录中生成的计数器模块进行代码审查，检查：
1. 语法正确性
2. 时序设计合理性
3. 端口定义完整性
4. 代码风格规范

如果发现问题，请提供修复建议。
同时生成对应的测试台进行功能验证。
"""
    
    print("📋 任务类型: 代码审查任务")
    print("🎯 期望选择: RealCodeReviewAgent")
    
    start_time = time.time()
    result2 = await coordinator.coordinate_task_execution(review_task)
    time2 = time.time() - start_time
    
    print(f"⏱️ 执行时间: {time2:.2f}秒")
    # 处理协调器返回的字典格式
    result2_str = str(result2) if isinstance(result2, dict) else result2
    print(f"✅ 任务完成: {'成功' if '审查' in result2_str or 'review' in result2_str.lower() else '失败'}")
    
    # 测试场景3: 混合任务 - 测试协调器的任务分解能力
    print(f"\n🔧 测试场景3: 复杂任务分解与协作")
    print("-" * 40)
    
    complex_task = """
请完成一个完整的UART模块开发与验证流程：

阶段1: 设计UART发送器模块
- 支持可配置波特率
- 8位数据，1个停止位，无校验
- 包含发送使能和忙状态信号

阶段2: 代码审查与测试
- 检查设计的正确性
- 生成综合测试台
- 执行功能仿真验证
- 提供性能分析报告

这个任务需要设计和审查智能体协作完成。
"""
    
    print("📋 任务类型: 复杂协作任务")
    print("🎯 期望行为: 智能体协作")
    
    start_time = time.time()
    result3 = await coordinator.coordinate_task_execution(complex_task)
    time3 = time.time() - start_time
    
    print(f"⏱️ 执行时间: {time3:.2f}秒")
    # 处理协调器返回的字典格式
    result3_str = str(result3) if isinstance(result3, dict) else result3
    print(f"✅ 任务完成: {'成功' if len(result3_str) > 200 else '失败'}")
    
    # 分析协调器性能
    print(f"\n📊 协调器性能分析")
    print("="*60)
    
    total_time = time1 + time2 + time3
    print(f"⏱️ 总执行时间: {total_time:.2f}秒")
    print(f"📈 平均任务时间: {total_time/3:.2f}秒")
    
    # 检查生成的文件数量
    artifacts_dir = log_session.get_artifacts_dir()
    verilog_files = list(artifacts_dir.glob("**/*.v"))
    test_files = list(artifacts_dir.glob("**/*test*.v")) + list(artifacts_dir.glob("**/*tb.v"))
    report_files = list(artifacts_dir.glob("**/*.md")) + list(artifacts_dir.glob("**/*.json"))
    
    print(f"📁 生成文件统计:")
    print(f"  📄 Verilog模块: {len(verilog_files)}个")
    print(f"  🧪 测试文件: {len(test_files)}个") 
    print(f"  📋 报告文件: {len(report_files)}个")
    
    # 智能体协作效果评估
    collaboration_success = 0
    if len(result1_str) > 100:  # 设计任务成功
        collaboration_success += 33.3
    if '审查' in result2_str or 'review' in result2_str.lower():  # 审查任务成功
        collaboration_success += 33.3
    if len(result3_str) > 200:  # 复杂任务成功
        collaboration_success += 33.4
    
    print(f"\n🤝 智能体协作评分: {collaboration_success:.1f}%")
    
    if collaboration_success >= 80:
        print("🌟 协调器表现优秀: 智能选择和任务分配能力强")
    elif collaboration_success >= 60:
        print("🔶 协调器表现良好: 基础协作功能正常")
    else:
        print("❌ 协调器需要改进: 任务分配或协作存在问题")
    
    # 详细结果展示
    print(f"\n📋 详细执行结果:")
    print(f"设计任务结果长度: {len(result1_str)} 字符")
    print(f"审查任务结果长度: {len(result2_str)} 字符")
    print(f"复杂任务结果长度: {len(result3_str)} 字符")
    
    return {
        "collaboration_score": collaboration_success,
        "total_time": total_time,
        "files_generated": len(verilog_files) + len(test_files) + len(report_files),
        "results": [result1_str, result2_str, result3_str]
    }


async def test_direct_agent_calling():
    """对比测试：直接调用智能体 vs 通过协调器调用"""
    print(f"\n🔄 对比测试: 直接调用 vs 协调器调用")
    print("="*60)
    
    config = FrameworkConfig.from_env()
    verilog_agent = RealVerilogDesignAgent(config)
    
    simple_task = "请设计一个简单的2输入AND门模块，包含基本的端口定义。"
    
    # 直接调用智能体
    print("🎯 直接调用VerilogAgent...")
    start_time = time.time()
    direct_result = await verilog_agent.process_with_function_calling(simple_task, max_iterations=5)
    direct_time = time.time() - start_time
    
    print(f"⏱️ 直接调用时间: {direct_time:.2f}秒")
    print(f"✅ 直接调用结果: {'成功' if len(direct_result) > 50 else '失败'}")
    
    # 通过协调器调用
    print("\n🧠 通过协调器调用...")
    coordinator = CentralizedCoordinator(config)
    coordinator.register_agent(verilog_agent)
    
    start_time = time.time()
    coordinator_result = await coordinator.coordinate_task_execution(simple_task)
    coordinator_time = time.time() - start_time
    
    print(f"⏱️ 协调器调用时间: {coordinator_time:.2f}秒")
    print(f"✅ 协调器调用结果: {'成功' if len(coordinator_result) > 50 else '失败'}")
    
    # 性能对比
    print(f"\n📊 性能对比:")
    print(f"直接调用: {direct_time:.2f}秒 ({len(direct_result)}字符)")
    print(f"协调器调用: {coordinator_time:.2f}秒 ({len(coordinator_result)}字符)")
    
    overhead = (coordinator_time - direct_time) / direct_time * 100 if direct_time > 0 else 0
    print(f"协调器开销: {overhead:+.1f}%")
    
    return {
        "direct_time": direct_time,
        "coordinator_time": coordinator_time,
        "overhead_percent": overhead
    }


async def main():
    """主测试函数"""
    print("🚀 启动协调器智能选择与调度测试")
    print("="*60)
    
    try:
        # 主要测试：协调器智能能力
        main_results = await test_coordinator_intelligence()
        
        # 对比测试：性能分析
        comparison_results = await test_direct_agent_calling()
        
        print(f"\n🎉 测试完成！")
        print(f"🤝 协作能力: {main_results['collaboration_score']:.1f}%")
        print(f"⏱️ 总耗时: {main_results['total_time']:.2f}秒")
        print(f"📁 生成文件: {main_results['files_generated']}个")
        print(f"📊 协调器开销: {comparison_results['overhead_percent']:+.1f}%")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'✅ 测试成功完成!' if success else '❌ 测试失败!'}")
    sys.exit(0 if success else 1)