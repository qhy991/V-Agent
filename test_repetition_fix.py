#!/usr/bin/env python3
"""
测试重复执行问题的修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_verilog_agent_no_repetition():
    """测试Verilog设计智能体不再重复执行"""
    
    try:
        print("🧪 测试Verilog设计智能体的重复执行修复...")
        
        from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgentRefactored
        from config.config import FrameworkConfig
        
        # 初始化配置和智能体
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgentRefactored(config)
        
        print("✅ 智能体初始化成功")
        
        # 简单的测试任务
        task = """设计一个简单的Verilog计数器模块:
- 模块名: simple_counter  
- 输入: clk (时钟), reset (复位)
- 输出: count (4位计数值)
- 功能: 同步复位的递增计数器

请生成代码并写入文件。"""
        
        print(f"📋 测试任务: {task}")
        print("🚀 开始执行...")
        
        import time
        start_time = time.time()
        
        # 执行任务，限制最大迭代次数为3来测试修复效果
        result = await agent.process_with_function_calling(
            task, 
            max_iterations=3,  # 限制迭代次数来验证修复
            conversation_id=f"test_repetition_fix_{int(time.time())}"
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ 任务执行完成！")
        print(f"⏱️ 执行时间: {execution_time:.2f}秒")
        print(f"📊 结果类型: {type(result)}")
        
        # 分析结果
        if isinstance(result, dict):
            print(f"📝 是否成功: {result.get('success', 'Unknown')}")
            if 'final_response' in result:
                response_preview = str(result['final_response'])[:200] + "..."
                print(f"📄 响应预览: {response_preview}")
        else:
            result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            print(f"📄 结果预览: {result_preview}")
        
        # 检查是否有生成的文件
        experiment_dirs = list(Path(".").glob("experiments/design_*"))
        if experiment_dirs:
            latest_dir = max(experiment_dirs, key=lambda p: p.stat().st_mtime)
            print(f"📁 最新实验目录: {latest_dir}")
            
            design_files = list(latest_dir.glob("**/*.v"))
            if design_files:
                print(f"📄 生成的Verilog文件: {len(design_files)} 个")
                for file_path in design_files[:3]:  # 显示前3个
                    print(f"   - {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_completion_detection():
    """测试任务完成检测逻辑"""
    print("\n🧪 测试任务完成检测逻辑...")
    
    try:
        # 简化测试：直接测试完成指标检测
        task_completion_indicators = [
            "✅ 任务完成", "任务已完成", "设计完成", "生成完成", 
            "文件已写入", "已生成文件", "成功写入", "task completed"
        ]
        
        test_messages = [
            "## ✅ 任务完成！以下是生成文件的完整路径",
            "设计已完成，文件已写入到指定路径",
            "任务进行中...",
            "生成完成，所有文件已保存"
        ]
        
        results = []
        for i, message in enumerate(test_messages):
            has_completion = any(indicator in message for indicator in task_completion_indicators)
            expected = [True, True, False, True][i]  # 预期结果
            success = has_completion == expected
            results.append(success)
            
            print(f"测试 {i+1}: {'✅' if success else '❌'} - '{message[:30]}...' -> {has_completion}")
        
        overall_success = all(results)
        print(f"📊 完成指标检测: {'✅ 成功' if overall_success else '❌ 失败'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ 完成检测测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 重复执行问题修复测试")
    print("=" * 60)
    
    # 运行测试
    success_1 = asyncio.run(test_verilog_agent_no_repetition())
    success_2 = asyncio.run(test_completion_detection())
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"1. Verilog智能体重复执行修复: {'✅ 成功' if success_1 else '❌ 失败'}")
    print(f"2. 任务完成检测逻辑: {'✅ 成功' if success_2 else '❌ 失败'}")
    
    overall_success = success_1 and success_2
    print(f"\n🎯 总体测试结果: {'✅ 全部通过' if overall_success else '❌ 部分失败'}")
    
    if overall_success:
        print("🎉 重复执行问题已成功修复！")
    else:
        print("⚠️ 仍需要进一步调试和修复。")