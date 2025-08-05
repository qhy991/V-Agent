#!/usr/bin/env python3
"""
测试System Prompt修复效果
验证强化的工具调用指导是否有效
"""

import os
import sys
import re
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_system_prompt_content():
    """测试System Prompt内容是否包含正确的指导"""
    print("🧪 测试System Prompt内容...")
    
    # 模拟LLMCoordinatorAgent
    try:
        from core.llm_coordinator_agent import LLMCoordinatorAgent
        from config.config import FrameworkConfig
        
        # 创建协调器实例
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        # 获取System Prompt
        system_prompt = coordinator._build_enhanced_system_prompt()
        
        # 验证关键内容
        checks = [
            ("包含禁止事项标题", "🚨🚨🚨 绝对禁止事项 🚨🚨🚨" in system_prompt),
            ("禁止enhanced_real_verilog_agent", "❌ enhanced_real_verilog_agent" in system_prompt),
            ("禁止enhanced_real_code_review_agent", "❌ enhanced_real_code_review_agent" in system_prompt),
            ("要求使用assign_task_to_agent", "assign_task_to_agent" in system_prompt),
            ("包含正确示例", "✅ 正确示例" in system_prompt),
            ("包含错误示例", "❌❌❌ 错误示例" in system_prompt),
            ("强调agent_id参数", "agent_id" in system_prompt),
            ("包含JSON格式要求", '"tool_calls"' in system_prompt)
        ]
        
        passed_checks = 0
        for description, check in checks:
            if check:
                print(f"  ✅ {description}")
                passed_checks += 1
            else:
                print(f"  ❌ {description}")
        
        success_rate = passed_checks / len(checks)
        print(f"\n📊 System Prompt检查结果: {passed_checks}/{len(checks)} ({success_rate:.1%})")
        
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ System Prompt测试失败: {str(e)}")
        return False

def test_forced_coordination_task():
    """测试强制协调任务的内容"""
    print("\n🧪 测试强制协调任务...")
    
    try:
        from core.llm_coordinator_agent import LLMCoordinatorAgent, TaskContext
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        # 创建模拟任务上下文
        task_context = TaskContext(
            task_id="test_task",
            original_request="设计一个计数器"
        )
        
        # 获取强制协调任务
        forced_task = coordinator._build_forced_coordination_task(
            "设计一个计数器模块", 
            task_context
        )
        
        # 验证关键内容
        checks = [
            ("包含强制指令标题", "🚨🚨🚨 强制指令 🚨🚨🚨" in forced_task),
            ("禁止智能体名称", "❌ enhanced_real_verilog_agent" in forced_task),
            ("要求identify_task_type", "identify_task_type" in forced_task),
            ("包含JSON示例", '"tool_calls"' in forced_task),
            ("包含严格要求", "🚨🚨🚨 严格要求 🚨🚨🚨" in forced_task),
            ("强调立即执行", "⚡ 立即执行" in forced_task)
        ]
        
        passed_checks = 0
        for description, check in checks:
            if check:
                print(f"  ✅ {description}")
                passed_checks += 1
            else:
                print(f"  ❌ {description}")
        
        success_rate = passed_checks / len(checks)
        print(f"\n📊 强制协调任务检查结果: {passed_checks}/{len(checks)} ({success_rate:.1%})")
        
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ 强制协调任务测试失败: {str(e)}")
        return False

def test_tool_name_detection():
    """测试工具名称检测逻辑"""
    print("\n🧪 测试工具名称检测逻辑...")
    
    # 模拟LLM响应
    test_cases = [
        # 错误的调用方式（应该被检测并阻止）
        {
            "input": '{"tool_calls": [{"tool_name": "enhanced_real_verilog_agent", "parameters": {}}]}',
            "description": "直接调用智能体名称",
            "should_detect": True,
            "is_correct": False
        },
        
        # 正确的调用方式
        {
            "input": '{"tool_calls": [{"tool_name": "assign_task_to_agent", "parameters": {"agent_id": "enhanced_real_verilog_agent"}}]}',
            "description": "正确使用assign_task_to_agent",
            "should_detect": True,
            "is_correct": True
        },
        
        # 其他正确调用
        {
            "input": '{"tool_calls": [{"tool_name": "identify_task_type", "parameters": {}}]}',
            "description": "调用identify_task_type",
            "should_detect": True,
            "is_correct": True
        }
    ]
    
    correct_detections = 0
    total_cases = len(test_cases)
    
    try:
        from core.llm_coordinator_agent import LLMCoordinatorAgent
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        
        for i, case in enumerate(test_cases):
            detected = coordinator._has_executed_tools(case["input"])
            
            print(f"  测试用例 {i+1}: {case['description']}")
            print(f"    输入: {case['input'][:50]}...")
            print(f"    检测结果: {detected}")
            print(f"    预期检测: {case['should_detect']}")
            
            if detected == case["should_detect"]:
                print(f"    ✅ 检测正确")
                correct_detections += 1
            else:
                print(f"    ❌ 检测错误")
            print()
        
        success_rate = correct_detections / total_cases
        print(f"📊 工具检测结果: {correct_detections}/{total_cases} ({success_rate:.1%})")
        
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"❌ 工具检测测试失败: {str(e)}")
        return False

def analyze_system_prompt_strength():
    """分析System Prompt的强度和清晰度"""
    print("\n🧪 分析System Prompt强度...")
    
    try:
        from core.llm_coordinator_agent import LLMCoordinatorAgent
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        coordinator = LLMCoordinatorAgent(config)
        system_prompt = coordinator._build_enhanced_system_prompt()
        
        # 分析指标
        metrics = {
            "总长度": len(system_prompt),
            "禁止语句数量": len(re.findall(r'[❌🚨].*?(禁止|绝对|不要|不能)', system_prompt)),
            "正确示例数量": len(re.findall(r'✅.*?示例', system_prompt)),
            "错误示例数量": len(re.findall(r'❌.*?示例', system_prompt)),
            "强调标记数量": len(re.findall(r'🚨', system_prompt)),
            "JSON代码块数量": len(re.findall(r'```json', system_prompt))
        }
        
        print("📊 System Prompt分析:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value}")
        
        # 评估强度
        strength_score = 0
        if metrics["总长度"] > 2000:
            strength_score += 20
        if metrics["禁止语句数量"] > 5:
            strength_score += 20
        if metrics["正确示例数量"] >= 3:
            strength_score += 20
        if metrics["错误示例数量"] >= 1:
            strength_score += 20
        if metrics["强调标记数量"] > 10:
            strength_score += 20
        
        print(f"\n📈 System Prompt强度评分: {strength_score}/100")
        
        if strength_score >= 80:
            print("✅ System Prompt强度充足")
            return True
        else:
            print("⚠️ System Prompt强度不足，建议进一步强化")
            return False
            
    except Exception as e:
        print(f"❌ System Prompt分析失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试System Prompt修复效果...\n")
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("System Prompt内容测试", test_system_prompt_content),
        ("强制协调任务测试", test_forced_coordination_task),
        ("工具名称检测测试", test_tool_name_detection),
        ("System Prompt强度分析", analyze_system_prompt_strength)
    ]
    
    for test_name, test_func in tests:
        print(f"" + "="*50)
        result = test_func()
        test_results.append((test_name, result))
    
    # 总结结果
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = passed_tests / len(test_results)
    print(f"\n🎯 总体成功率: {passed_tests}/{len(test_results)} ({success_rate:.1%})")
    
    if success_rate >= 0.75:
        print("🎉 修复效果良好，System Prompt已显著强化！")
        print("\n建议:")
        print("1. 重新运行原失败的测试用例")
        print("2. 监控LLM的工具调用行为")
        print("3. 如有必要，进一步调整指导语句")
    else:
        print("⚠️ 修复效果不够理想，建议进一步改进")
        print("\n建议:")
        print("1. 增加更多禁止语句")
        print("2. 提供更多具体示例")
        print("3. 使用更强的视觉强调")
    
    return success_rate >= 0.75

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)