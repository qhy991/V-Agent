#!/usr/bin/env python3
"""
高级工具交互和错误处理能力测试
Advanced Tool Interaction and Error Handling Test

专门测试：
1. 复杂的工具调用链执行
2. 智能错误处理和修复能力
3. 工具间的数据传递和协作
4. 迭代修复和优化能力
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from agents.real_code_reviewer import RealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging


async def test_complex_tool_chain():
    """测试复杂的工具调用链"""
    print("🔧 复杂工具调用链测试")
    print("="*50)
    
    # 初始化
    config = FrameworkConfig.from_env()
    log_session = setup_enhanced_logging("tool_chain_test")
    agent = RealCodeReviewAgent(config)
    
    print(f"📂 工作目录: {log_session.get_artifacts_dir()}")
    
    # 复杂的工具调用链任务
    complex_chain_task = """
请执行以下复杂的工具调用链，展示多个工具的协调配合：

🔗 工具调用链任务：
1. **文件读取**: 尝试读取一个不存在的配置文件 "project_config.json"
2. **智能创建**: 当文件不存在时，创建一个包含项目配置的JSON文件
3. **Verilog设计**: 基于配置创建一个可配置位宽的计数器模块
4. **语法检查**: 分析生成的Verilog代码质量
5. **测试台生成**: 为计数器模块生成综合测试台
6. **仿真执行**: 运行iverilog仿真验证功能
7. **构建脚本**: 生成Makefile构建脚本
8. **脚本执行**: 执行构建脚本进行编译

这个测试将验证：
- 多达8个工具的连续调用
- 文件间的数据传递
- 错误发生时的智能处理
- 基于前一步结果的决策制定

请按顺序执行每个步骤，并在每步完成后说明结果。
"""
    
    print("🎯 开始执行复杂工具调用链...")
    start_time = time.time()
    
    result = await agent.process_with_function_calling(
        complex_chain_task, 
        max_iterations=15  # 允许更多迭代来完成复杂链
    )
    
    execution_time = time.time() - start_time
    print(f"⏱️ 执行时间: {execution_time:.2f}秒")
    
    # 分析执行效果
    tool_calls_count = result.count("工具") + result.count("调用")
    files_created = result.count("写入") + result.count("创建") + result.count("生成")
    errors_handled = result.count("错误") + result.count("失败") + result.count("重试")
    
    print(f"📊 执行分析:")
    print(f"  🔧 工具调用次数: {tool_calls_count}")
    print(f"  📁 文件创建次数: {files_created}")
    print(f"  🚨 错误处理次数: {errors_handled}")
    print(f"  📝 结果长度: {len(result)} 字符")
    
    return {
        "execution_time": execution_time,
        "tool_calls": tool_calls_count,
        "files_created": files_created,
        "errors_handled": errors_handled,
        "success": len(result) > 500 and files_created > 0
    }


async def test_error_injection_recovery():
    """测试错误注入和智能恢复"""
    print(f"\n🚨 错误注入与智能恢复测试")
    print("="*50)
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 故意设计错误场景
    error_scenario_task = """
现在进行错误注入测试，请按以下步骤操作：

🚨 错误场景设计：
1. **路径错误**: 尝试读取路径 "/nonexistent/path/file.v" 的文件
2. **语法错误**: 创建一个包含多个语法错误的Verilog模块：
   - 缺少分号
   - 括号不匹配
   - 信号未声明
   - 模块定义不完整
3. **编译错误**: 尝试编译这个错误的模块
4. **智能修复**: 分析编译错误并逐步修复
5. **验证修复**: 重新编译确认修复效果
6. **功能测试**: 生成测试台验证功能正确性

重点要求：
- 展示每次错误的详细分析
- 说明修复策略和具体操作
- 统计修复尝试次数和成功率
- 验证最终的功能正确性

这将测试智能体的错误诊断、分析、修复和验证能力。
"""
    
    print("🎯 开始错误注入与恢复测试...")
    start_time = time.time()
    
    result = await agent.process_with_function_calling(
        error_scenario_task,
        max_iterations=12  # 允许多次修复尝试
    )
    
    execution_time = time.time() - start_time
    print(f"⏱️ 执行时间: {execution_time:.2f}秒")
    
    # 分析错误处理效果
    errors_detected = result.count("错误") + result.count("失败") + result.count("异常")
    fixes_attempted = result.count("修复") + result.count("调整") + result.count("重试")
    final_success = "成功" in result[-300:] or "完成" in result[-300:]
    
    print(f"📊 错误处理分析:")
    print(f"  🔍 检测到错误: {errors_detected} 次")
    print(f"  🔧 尝试修复: {fixes_attempted} 次") 
    print(f"  ✅ 最终成功: {'是' if final_success else '否'}")
    
    # 计算错误恢复率
    recovery_rate = (fixes_attempted / max(errors_detected, 1)) * 100
    print(f"  📈 错误恢复率: {recovery_rate:.1f}%")
    
    return {
        "execution_time": execution_time,
        "errors_detected": errors_detected,
        "fixes_attempted": fixes_attempted,
        "final_success": final_success,
        "recovery_rate": recovery_rate
    }


async def test_iterative_optimization():
    """测试迭代优化能力"""
    print(f"\n🔄 迭代优化能力测试")
    print("="*50)
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 迭代优化任务
    optimization_task = """
请进行迭代优化测试，展示持续改进能力：

🔄 迭代优化流程：
1. **初始设计**: 创建一个简单但低效的4位加法器
2. **性能分析**: 分析当前设计的性能瓶颈
3. **优化方案1**: 实施第一轮优化（如减少逻辑层数）
4. **效果评估**: 评估优化效果
5. **优化方案2**: 实施第二轮优化（如并行化改进）
6. **最终验证**: 生成测试台验证所有版本的功能一致性

优化目标：
- 减少逻辑延迟
- 优化资源使用
- 保持功能正确性
- 提高代码可读性

请详细记录每次优化的：
- 具体改进内容
- 预期效果分析
- 实际效果验证
- 下一步优化方向

展示智能体的持续改进和学习能力。
"""
    
    print("🎯 开始迭代优化测试...")
    start_time = time.time()
    
    result = await agent.process_with_function_calling(
        optimization_task,
        max_iterations=10
    )
    
    execution_time = time.time() - start_time
    print(f"⏱️ 执行时间: {execution_time:.2f}秒")
    
    # 分析优化效果
    versions_created = result.count("版本") + result.count("优化") + result.count("改进")
    analysis_performed = result.count("分析") + result.count("评估") + result.count("比较")
    improvements_made = result.count("改善") + result.count("提升") + result.count("优化")
    
    print(f"📊 优化过程分析:")
    print(f"  🔧 创建版本数: {versions_created}")
    print(f"  🔍 分析评估次数: {analysis_performed}")
    print(f"  📈 改进操作次数: {improvements_made}")
    
    return {
        "execution_time": execution_time,
        "versions_created": versions_created,
        "analysis_performed": analysis_performed,
        "improvements_made": improvements_made,
        "success": versions_created > 1 and improvements_made > 0
    }


async def test_file_collaboration():
    """测试文件协作和数据传递"""
    print(f"\n📁 文件协作与数据传递测试")
    print("="*50)
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    collaboration_task = """
测试智能体的文件协作和数据传递能力：

📁 文件协作流程：
1. **创建主模块**: 设计一个SPI主控制器模块
2. **保存设计文档**: 创建模块规格说明文档 (markdown格式)
3. **读取并分析**: 读取刚创建的文档，基于规格实现代码
4. **交叉验证**: 读取生成的代码，检查是否符合文档规格
5. **生成测试计划**: 创建详细的测试计划文档
6. **实施测试**: 根据测试计划生成测试台
7. **结果记录**: 创建测试结果报告
8. **整合打包**: 将所有文件组织成项目结构

文件类型要求：
- .v文件 (Verilog代码)
- .md文件 (文档说明)
- .json文件 (配置信息)
- 测试台和脚本文件

展示智能体在多文件项目中的协作管理能力。
"""
    
    print("🎯 开始文件协作测试...")
    start_time = time.time()
    
    result = await agent.process_with_function_calling(
        collaboration_task,
        max_iterations=12
    )
    
    execution_time = time.time() - start_time
    print(f"⏱️ 执行时间: {execution_time:.2f}秒")
    
    # 检查实际生成的文件
    log_session = setup_enhanced_logging("file_collab_check")  
    artifacts_dir = log_session.get_artifacts_dir()
    
    verilog_files = list(artifacts_dir.glob("**/*.v"))
    markdown_files = list(artifacts_dir.glob("**/*.md"))
    json_files = list(artifacts_dir.glob("**/*.json"))
    other_files = list(artifacts_dir.glob("**/*")) 
    
    total_files = len(verilog_files) + len(markdown_files) + len(json_files)
    
    print(f"📊 文件生成统计:")
    print(f"  📄 Verilog文件: {len(verilog_files)}个")
    print(f"  📝 Markdown文档: {len(markdown_files)}个")
    print(f"  ⚙️ JSON配置: {len(json_files)}个")
    print(f"  📦 总文件数: {total_files}个")
    
    # 分析文件协作效果
    file_operations = result.count("写入") + result.count("读取") + result.count("创建")
    cross_references = result.count("根据") + result.count("基于") + result.count("参考")
    
    return {
        "execution_time": execution_time,
        "files_generated": total_files,
        "file_operations": file_operations,
        "cross_references": cross_references,
        "success": total_files >= 3 and cross_references > 0
    }


async def main():
    """主测试函数"""
    print("🚀 启动高级工具交互和错误处理测试")
    print("="*60)
    
    try:
        # 测试1: 复杂工具调用链
        chain_results = await test_complex_tool_chain()
        
        # 测试2: 错误注入与恢复
        error_results = await test_error_injection_recovery()
        
        # 测试3: 迭代优化
        optimization_results = await test_iterative_optimization()
        
        # 测试4: 文件协作
        collaboration_results = await test_file_collaboration()
        
        # 综合评估
        print(f"\n📊 综合测试结果")
        print("="*60)
        
        total_time = sum([
            chain_results['execution_time'],
            error_results['execution_time'], 
            optimization_results['execution_time'],
            collaboration_results['execution_time']
        ])
        
        success_count = sum([
            chain_results['success'],
            error_results['final_success'],
            optimization_results['success'],
            collaboration_results['success']
        ])
        
        success_rate = success_count / 4 * 100
        
        print(f"⏱️ 总执行时间: {total_time:.2f}秒")
        print(f"✅ 成功率: {success_rate:.1f}% ({success_count}/4)")
        print(f"🔧 工具调用次数: {chain_results['tool_calls']}")
        print(f"📁 文件生成总数: {collaboration_results['files_generated']}")
        print(f"🚨 错误恢复率: {error_results['recovery_rate']:.1f}%")
        print(f"🔄 迭代优化次数: {optimization_results['improvements_made']}")
        
        # 能力评级
        if success_rate >= 75 and error_results['recovery_rate'] >= 80:
            print(f"\n🌟 综合评级: 优秀")
            print("   工具交互能力强，错误处理智能，协作效果好")
        elif success_rate >= 50 and error_results['recovery_rate'] >= 60:
            print(f"\n🔶 综合评级: 良好") 
            print("   基础功能正常，有进一步提升空间")
        else:
            print(f"\n❌ 综合评级: 需要改进")
            print("   工具交互或错误处理存在问题")
        
        return success_rate >= 50
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'✅ 高级工具交互测试成功!' if success else '❌ 测试失败!'}")
    sys.exit(0 if success else 1)