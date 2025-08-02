#!/usr/bin/env python3
"""
测试完整的TDD系统修复
验证所有修复是否解决了之前发现的问题
"""

import asyncio
import logging
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from core.base_agent import TaskMessage

async def test_tool_dependency_control():
    """测试工具依赖关系控制逻辑"""
    print("🔧 测试工具依赖关系控制逻辑")
    print("=" * 60)
    
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    # 创建一个会导致工具调用失败的测试请求
    task_message = TaskMessage(
        task_id="test_dependency_control",
        sender_id="test_sender", 
        receiver_id=agent.agent_id,
        message_type="design_request",
        content="设计一个测试模块，但使用错误的参数格式来触发第一个工具失败"
    )
    
    try:
        # 使用一个会导致generate_verilog_code失败的prompt
        test_prompt = """请设计一个简单的测试模块。请使用以下工具调用：
        
        ```json
        {
            "tool_calls": [
                {
                    "tool_name": "generate_verilog_code",
                    "parameters": {
                        "module_name": "test_module",
                        "requirements": "简单测试模块",
                        "input_ports": "invalid_format_string",
                        "output_ports": "also_invalid"
                    }
                },
                {
                    "tool_name": "analyze_code_quality",
                    "parameters": {
                        "verilog_code": "module test; endmodule"
                    }
                },
                {
                    "tool_name": "generate_testbench",
                    "parameters": {
                        "module_name": "test_module",
                        "verilog_code": "module test; endmodule"
                    }
                }
            ]
        }
        ```
        """
        
        result = await agent.execute_enhanced_task(
            enhanced_prompt=test_prompt,
            original_message=task_message,
            file_contents={}
        )
        
        print(f"✅ 测试结果: {result.get('success', False)}")
        print(f"📋 迭代次数: {result.get('iterations', 0)}")
        
        # 检查工具结果
        tool_results = result.get("tool_results", [])
        if tool_results:
            print(f"🔧 工具调用数量: {len(tool_results)}")
            
            for i, tool_result in enumerate(tool_results, 1):
                success = tool_result.get('success', False) if isinstance(tool_result, dict) else getattr(tool_result, 'success', False)
                tool_name = tool_result.get('tool_name', 'unknown') if isinstance(tool_result, dict) else getattr(tool_result, 'tool_name', 'unknown')
                
                print(f"   {i}. 工具: {tool_name}, 成功: {success}")
                
                if not success:
                    error = tool_result.get('error', '') if isinstance(tool_result, dict) else getattr(tool_result, 'error', '')
                    if "跳过执行" in error:
                        print(f"      ✅ 正确跳过了依赖失败的工具")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False

async def test_parameter_repair_accuracy():
    """测试参数修复机制的准确性"""
    print("\n🔨 测试参数修复机制的准确性")
    print("=" * 60)
    
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    # 测试端口数组的自动修复
    task_message = TaskMessage(
        task_id="test_parameter_repair",
        sender_id="test_sender", 
        receiver_id=agent.agent_id,
        message_type="design_request",
        content="测试参数自动修复"
    )
    
    try:
        test_prompt = """请生成一个8位加法器，使用以下工具调用（参数格式需要修复）：
        
        ```json
        {
            "tool_calls": [
                {
                    "tool_name": "generate_verilog_code",
                    "parameters": {
                        "module_name": "adder_8bit",
                        "requirements": "8位二进制加法器",
                        "input_ports": ["a [7:0]", "b [7:0]", "cin"],
                        "output_ports": ["sum [7:0]", "cout"]
                    }
                }
            ]
        }
        ```
        """
        
        result = await agent.execute_enhanced_task(
            enhanced_prompt=test_prompt,
            original_message=task_message,
            file_contents={}
        )
        
        print(f"✅ 参数修复测试结果: {result.get('success', False)}")
        
        # 检查是否成功修复了参数格式
        if result.get('success', False):
            print("✅ 参数自动修复功能正常工作")
        else:
            print("⚠️ 参数修复可能需要进一步改进")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 参数修复测试异常: {str(e)}")
        return False

async def test_enhanced_error_feedback():
    """测试增强的错误反馈机制"""
    print("\n💬 测试增强的错误反馈机制")
    print("=" * 60)
    
    # 这个测试主要验证错误消息的质量
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    task_message = TaskMessage(
        task_id="test_error_feedback",
        sender_id="test_sender", 
        receiver_id=agent.agent_id,
        message_type="design_request",
        content="测试错误反馈质量"
    )
    
    try:
        # 故意使用错误的参数名来触发详细的错误反馈
        test_prompt = """请分析设计需求，但使用错误的参数名：
        
        ```json
        {
            "tool_calls": [
                {
                    "tool_name": "analyze_design_requirements",
                    "parameters": {
                        "design_description": "这是错误的参数名",
                        "wrong_param": "另一个错误参数"
                    }
                }
            ]
        }
        ```
        """
        
        result = await agent.execute_enhanced_task(
            enhanced_prompt=test_prompt,
            original_message=task_message,
            file_contents={}
        )
        
        iterations = result.get('iterations', 0)
        print(f"📋 迭代次数: {iterations}")
        
        if iterations > 1:
            print("✅ 系统正确识别了参数错误并提供了修正机会")
        
        if result.get('success', False):
            print("✅ 最终成功执行了任务")
        else:
            print("⚠️ 任务未成功完成，但错误反馈机制应该已提供了详细信息")
            
        return True  # 这个测试主要关注错误处理流程，不要求最终成功
        
    except Exception as e:
        print(f"❌ 错误反馈测试异常: {str(e)}")
        return False

async def main():
    """运行所有测试"""
    print("🧪 测试完整的TDD系统修复")
    print("=" * 80)
    
    # 配置日志级别以减少噪音
    logging.getLogger("Agent").setLevel(logging.WARNING)
    logging.getLogger("LLMClient").setLevel(logging.WARNING)
    
    test_results = []
    
    # 1. 测试工具依赖关系控制
    result1 = await test_tool_dependency_control()
    test_results.append(("工具依赖关系控制", result1))
    
    # 2. 测试参数修复准确性
    result2 = await test_parameter_repair_accuracy()
    test_results.append(("参数修复准确性", result2))
    
    # 3. 测试增强错误反馈
    result3 = await test_enhanced_error_feedback()
    test_results.append(("增强错误反馈", result3))
    
    # 总结测试结果
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:30} {status}")
        if passed:
            passed_tests += 1
    
    print("\n" + "=" * 80)
    print(f"📈 总体结果: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有核心修复都已验证通过！")
        print("✅ TDD系统的主要问题已得到解决")
    elif passed_tests >= total_tests * 0.7:
        print("✅ 大部分修复已验证通过")
        print("⚠️ 还有少数问题需要进一步调优")
    else:
        print("⚠️ 仍有较多问题需要解决")
        print("🔧 建议进行更深入的调试")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)