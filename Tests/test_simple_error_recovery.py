#!/usr/bin/env python3
"""
简化的错误恢复能力测试
Simple Error Recovery Test
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from agents.real_code_reviewer import RealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging


async def test_error_recovery():
    """测试错误恢复能力"""
    print("🧪 简化的错误恢复能力测试")
    print("=" * 50)
    
    # 初始化
    log_session = setup_enhanced_logging("error_recovery_test")
    print(f"📁 实验目录: {log_session.session_log_dir}")
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 创建测试目录和文件
    test_dir = Path("error_recovery_test")
    test_dir.mkdir(exist_ok=True)
    
    # 测试1: 语法错误修复
    print("\n🎯 测试1: 基础语法错误修复")
    print("-" * 30)
    
    # 创建有明显语法错误的文件
    error_file = test_dir / "bad_syntax.v"
    error_file.write_text('''
module bad_syntax(input clk, output reg count);
    always @(posedge clk) begin
        count <= count + 1  // 缺少分号 - 明显的语法错误
    end
endmodule
''')
    
    task1 = f"""
请处理这个Verilog文件的编译错误：

1. 读取文件：{error_file}
2. 尝试编译（会失败）
3. 分析错误并修复语法问题
4. 保存修复后的文件为 fixed_syntax.v
5. 重新编译验证修复成功

文件包含明显的语法错误，请展示错误识别和修复过程。
"""
    
    start_time = time.time()
    result1 = await agent.process_with_function_calling(
        user_request=task1,
        max_iterations=6  # 限制迭代次数
    )
    execution_time1 = time.time() - start_time
    
    print(f"⏱️ 执行时间: {execution_time1:.2f}秒")
    
    # 分析结果中的关键迭代信息
    error_detected = "错误" in result1 or "error" in result1.lower()
    fix_attempted = "修复" in result1 or "fix" in result1.lower()
    iteration_evident = "tool_calls" in result1 or "工具调用" in result1
    
    print(f"📊 能力分析:")
    print(f"  错误检测: {'✅' if error_detected else '❌'}")
    print(f"  修复尝试: {'✅' if fix_attempted else '❌'}")
    print(f"  迭代调用: {'✅' if iteration_evident else '❌'}")
    
    # 测试2: 文件路径错误恢复
    print("\n🎯 测试2: 文件路径错误恢复")
    print("-" * 30)
    
    task2 = f"""
请尝试构建一个不存在的项目：

1. 尝试读取不存在的文件：nonexistent.v
2. 当发现文件不存在时，创建一个简单的AND门模块
3. 生成构建脚本并编译
4. 展示从"文件不存在"到"成功构建"的完整过程

要求展示错误恢复的完整流程。
"""
    
    start_time = time.time()
    result2 = await agent.process_with_function_calling(
        user_request=task2,
        max_iterations=5
    )
    execution_time2 = time.time() - start_time
    
    print(f"⏱️ 执行时间: {execution_time2:.2f}秒")
    
    # 分析恢复能力
    file_not_found = "不存在" in result2 or "not found" in result2.lower()
    recovery_action = "创建" in result2 or "create" in result2.lower()
    successful_build = "成功" in result2 or "success" in result2.lower()
    
    print(f"📊 恢复能力分析:")
    print(f"  错误识别: {'✅' if file_not_found else '❌'}")
    print(f"  恢复行动: {'✅' if recovery_action else '❌'}")
    print(f"  最终成功: {'✅' if successful_build else '❌'}")
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 错误恢复能力评估")
    print("=" * 50)
    
    total_time = execution_time1 + execution_time2
    print(f"🕒 总测试时间: {total_time:.2f}秒")
    
    # 综合评分
    capabilities = [
        error_detected, fix_attempted, iteration_evident,
        file_not_found, recovery_action, successful_build
    ]
    score = sum(capabilities) / len(capabilities) * 100
    
    print(f"📊 综合能力评分: {score:.1f}%")
    
    if score >= 80:
        print("✅ 智能体具备优秀的错误处理和迭代能力")
    elif score >= 60:
        print("🔶 智能体具备基础的错误处理能力，有改进空间")
    else:
        print("❌ 智能体的错误处理能力需要进一步增强")
    
    # 具体建议
    print("\n💡 能力分析:")
    if not iteration_evident:
        print("  - 需要加强工具链式调用的迭代逻辑")
    if not fix_attempted:
        print("  - 需要增强基于错误信息的修复策略")
    if not recovery_action:
        print("  - 需要改进异常情况下的恢复机制")
    
    return score >= 60


if __name__ == "__main__":
    success = asyncio.run(test_error_recovery())
    print(f"\n🎯 测试结果: {'通过' if success else '需要改进'}")