#!/usr/bin/env python3
"""
演示如何使用实验文件进行可视化
Demo: How to use experiment files for visualization
"""

import json
import os
from pathlib import Path
from datetime import datetime

def demo_experiment_analysis():
    """演示实验数据分析"""
    print("🎯 V-Agent 实验可视化演示")
    print("=" * 50)
    
    # 1. 加载实验报告
    experiment_id = "llm_coordinator_counter_1754463430"
    report_path = Path("llm_experiments") / experiment_id / "reports" / "experiment_report.json"
    
    print(f"🔍 检查文件路径: {report_path}")
    print(f"   文件存在: {report_path.exists()}")
    
    if not report_path.exists():
        print(f"❌ 实验报告文件不存在: {report_path}")
        # 尝试查找其他可能的路径
        possible_paths = [
            Path("llm_experiments") / experiment_id / "reports" / "experiment_report.json",
            Path("experiments") / experiment_id / "reports" / "experiment_report.json",
            Path("reports") / "experiment_report.json"
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"✅ 找到替代路径: {path}")
                report_path = path
                break
        else:
            print("❌ 未找到任何实验报告文件")
            return
    
    print(f"📊 加载实验报告: {report_path}")
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            experiment_data = json.load(f)
        print("✅ 成功加载实验报告")
    except Exception as e:
        print(f"❌ 加载实验报告失败: {e}")
        return
    
    # 2. 显示实验基本信息
    print("\n📋 实验基本信息:")
    print(f"   实验ID: {experiment_data.get('experiment_id', 'N/A')}")
    print(f"   设计类型: {experiment_data.get('design_type', 'N/A')}")
    print(f"   执行状态: {'✅ 成功' if experiment_data.get('success') else '❌ 失败'}")
    print(f"   任务耗时: {experiment_data.get('task_duration', 0):.2f} 秒")
    
    # 3. 分析智能体交互
    print("\n🤖 智能体交互分析:")
    agent_interactions = experiment_data.get('agent_interactions', [])
    if agent_interactions:
        for i, interaction in enumerate(agent_interactions, 1):
            agent_id = interaction.get('target_agent_id', 'unknown')
            execution_time = interaction.get('execution_time', 0)
            response_length = interaction.get('response_length', 0)
            success = interaction.get('success', False)
            
            print(f"   {i}. {agent_id}")
            print(f"      执行时间: {execution_time:.2f} 秒")
            print(f"      响应长度: {response_length} 字符")
            print(f"      状态: {'✅ 成功' if success else '❌ 失败'}")
    else:
        print("   暂无智能体交互数据")
    
    # 4. 分析工作流阶段
    print("\n🔄 工作流阶段分析:")
    workflow_stages = experiment_data.get('workflow_stages', [])
    if workflow_stages:
        for i, stage in enumerate(workflow_stages, 1):
            stage_name = stage.get('stage_name', 'unknown')
            duration = stage.get('duration', 0)
            success = stage.get('success', False)
            agent_id = stage.get('agent_id', 'unknown')
            
            print(f"   {i}. {stage_name}")
            print(f"      智能体: {agent_id}")
            print(f"      耗时: {duration:.2f} 秒")
            print(f"      状态: {'✅ 成功' if success else '❌ 失败'}")
    else:
        print("   暂无工作流阶段数据")
    
    # 5. 显示生成的文件
    print("\n📁 生成的文件:")
    designs_path = Path("llm_experiments") / experiment_id / "designs"
    testbenches_path = Path("llm_experiments") / experiment_id / "testbenches"
    
    if designs_path.exists():
        print("   📂 设计文件:")
        for file in designs_path.glob("*.v"):
            size = file.stat().st_size
            print(f"      📄 {file.name} ({size} bytes)")
    else:
        print("   📂 设计文件目录不存在")
    
    if testbenches_path.exists():
        print("   📂 测试台文件:")
        for file in testbenches_path.glob("*.v"):
            size = file.stat().st_size
            print(f"      📄 {file.name} ({size} bytes)")
    else:
        print("   📂 测试台文件目录不存在")
    
    # 6. 显示代码内容
    print("\n💻 代码内容预览:")
    design_file = designs_path / "counter_v2.v"
    if design_file.exists():
        print("   📄 Verilog设计代码:")
        try:
            with open(design_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                for i, line in enumerate(lines[:5], 1):
                    print(f"      {i:2d}: {line}")
                if len(lines) > 5:
                    print(f"      ... (共 {len(lines)} 行)")
        except Exception as e:
            print(f"      ❌ 读取文件失败: {e}")
    else:
        print("   📄 Verilog设计代码文件不存在")
    
    # 7. 性能统计
    print("\n📈 性能统计:")
    total_execution_time = sum(stage.get('duration', 0) for stage in workflow_stages)
    total_interactions = len(agent_interactions)
    success_rate = sum(1 for stage in workflow_stages if stage.get('success', False)) / len(workflow_stages) if workflow_stages else 0
    
    print(f"   总执行时间: {total_execution_time:.2f} 秒")
    print(f"   智能体交互次数: {total_interactions}")
    print(f"   成功率: {success_rate:.1%}")
    
    # 8. 错误分析
    print("\n⚠️ 错误分析:")
    # 检查是否有失败的阶段
    failed_stages = [stage for stage in workflow_stages if not stage.get('success', True)]
    if failed_stages:
        print("   发现失败的阶段:")
        for stage in failed_stages:
            print(f"     - {stage.get('stage_name', 'unknown')}")
    else:
        print("   ✅ 所有阶段都成功完成")
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("\n💡 使用建议:")
    print("   1. 运行 'python experiment_visualizer.py' 启动完整可视化界面")
    print("   2. 查看 'visualization_guide.md' 了解详细使用方法")
    print("   3. 修改 experiment_visualizer.py 中的实验ID来可视化其他实验")

def demo_log_analysis():
    """演示日志文件分析"""
    print("\n📝 日志文件分析演示")
    print("=" * 30)
    
    log_file = "counter_test_utf8_fixed_20250806_145707.txt"
    print(f"🔍 检查日志文件: {log_file}")
    print(f"   文件存在: {os.path.exists(log_file)}")
    
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    print(f"📊 分析日志文件: {log_file}")
    
    # 统计日志信息
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"   总行数: {len(lines)}")
        
        # 统计不同类型的日志
        info_count = sum(1 for line in lines if "INFO" in line)
        warning_count = sum(1 for line in lines if "WARNING" in line)
        error_count = sum(1 for line in lines if "ERROR" in line)
        
        print(f"   INFO日志: {info_count} 条")
        print(f"   WARNING日志: {warning_count} 条")
        print(f"   ERROR日志: {error_count} 条")
        
        # 统计智能体活动
        agent_activities = {}
        for line in lines:
            if "Agent." in line:
                parts = line.split(" - ")
                if len(parts) >= 2:
                    agent_part = parts[1]
                    if agent_part.startswith("Agent."):
                        agent_name = agent_part.split(" - ")[0]
                        agent_activities[agent_name] = agent_activities.get(agent_name, 0) + 1
        
        print("\n🤖 智能体活动统计:")
        for agent, count in agent_activities.items():
            print(f"   {agent}: {count} 条日志")
        
        # 查找关键事件
        print("\n🔍 关键事件:")
        key_events = [
            "开始协调任务",
            "工具执行成功",
            "工具执行失败",
            "任务完成",
            "编译失败"
        ]
        
        for event in key_events:
            count = sum(1 for line in lines if event in line)
            if count > 0:
                print(f"   {event}: {count} 次")
                
    except Exception as e:
        print(f"❌ 分析日志文件失败: {e}")

if __name__ == "__main__":
    # 运行演示
    demo_experiment_analysis()
    demo_log_analysis() 