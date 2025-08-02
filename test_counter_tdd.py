#!/usr/bin/env python3
"""
Counter TDD测试 - 使用新的测试台验证完整TDD流程
"""

import asyncio
import tempfile
import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_counter_with_testbench():
    """测试带有测试台的counter TDD流程"""
    print("🎯 测试Counter TDD流程（带测试台）")
    
    try:
        from extensions.test_driven_coordinator import TestDrivenCoordinator
        from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
        from config.config import FrameworkConfig
        
        config = FrameworkConfig.from_env()
        base_coordinator = EnhancedCentralizedCoordinator(config)
        tdd_coordinator = TestDrivenCoordinator(base_coordinator)
        
        # Counter设计需求
        design_request = """
设计任务 (迭代 1):

设计一个8位计数器，具有以下功能：
- 同步时钟，异步复位
- 可控制的计数使能
- 可设置的计数模式(上计数/下计数)
- 计数值输出和溢出检测

模块接口：
```verilog
module counter_8bit (
    input        clk,       // 时钟
    input        rst_n,     // 异步复位（低电平有效）
    input        enable,    // 计数使能
    input        up_down,   // 计数方向(1:上计数, 0:下计数)
    output [7:0] count,     // 计数值
    output       overflow   // 溢出标志
);
```

🎯 功能要求：
1. 实现8位二进制计数器
2. 支持上计数和下计数模式
3. 正确处理溢出检测
4. 异步复位功能
5. 使能控制功能

💡 设计提示：
- 注意rst_n是低电平有效的异步复位
- 溢出检测应该在边界条件时正确设置
- 确保所有时序逻辑正确
"""
        
        print(f"📋 设计需求: Counter 8-bit with comprehensive testbench")
        
        # 指定使用新创建的测试台
        testbench_path = "/home/haiyan/Research/CentralizedAgentFramework/test_cases/counter_8bit_tb.v"
        
        # 验证测试台文件存在
        if not Path(testbench_path).exists():
            print(f"❌ 测试台文件不存在: {testbench_path}")
            return False
        
        print(f"✅ 使用测试台: {testbench_path}")
        
        # 运行TDD流程（使用execute_test_driven_task方法）
        result = await tdd_coordinator.execute_test_driven_task(
            task_description=design_request,
            testbench_path=testbench_path
        )
        
        if result.get('success'):
            print("✅ TDD循环成功完成")
            print(f"   总迭代次数: {result.get('total_iterations', 'N/A')}")
            print(f"   执行时长: {result.get('duration', 'N/A'):.2f}秒")
            
            # 检查生成的文件
            file_refs = result.get('file_references', [])
            if file_refs:
                print("📁 生成的文件:")
                for file_ref in file_refs:
                    if isinstance(file_ref, dict):
                        file_path = file_ref.get('file_path', 'Unknown')
                        if Path(file_path).exists():
                            print(f"   ✅ {file_path}")
                        else:
                            print(f"   ❌ {file_path} (文件不存在)")
                    else:
                        print(f"   📄 {file_ref}")
            
            # 检查是否有仿真输出
            conversation_history = result.get('conversation_history', [])
            if conversation_history:
                print("\n📊 执行概要:")
                for i, msg in enumerate(conversation_history[:3], 1):  # 只显示前3条
                    speaker = msg.get('speaker_id', 'Unknown')
                    task_result = msg.get('task_result', {})
                    success = task_result.get('success', False)
                    print(f"   {i}. {speaker}: {'✅ 成功' if success else '❌ 失败'}")
            
            return True
        else:
            print(f"❌ TDD循环失败: {result.get('error', 'Unknown error')}")
            if 'conversation_history' in result:
                print("🔍 错误详情:")
                for msg in result['conversation_history'][-2:]:  # 显示最后2条消息
                    speaker = msg.get('speaker_id', 'Unknown')
                    task_result = msg.get('task_result', {})
                    error = task_result.get('error')
                    if error:
                        print(f"   {speaker}: {error}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_testbench_content():
    """验证测试台内容是否正确"""
    print("\n🔍 验证测试台内容")
    
    testbench_path = "/home/haiyan/Research/CentralizedAgentFramework/test_cases/counter_8bit_tb.v"
    
    if not Path(testbench_path).exists():
        print("❌ 测试台文件不存在")
        return False
    
    try:
        with open(testbench_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键测试内容
        checks = [
            ("module counter_8bit_tb", "测试台模块声明"),
            ("counter_8bit uut", "被测模块实例化"),
            ("rst_n", "异步复位信号"),
            ("up_down", "计数方向信号"),
            ("overflow", "溢出检测信号"),
            ("task test_", "测试任务定义"),
            ("$dumpfile", "波形文件生成"),
            ("$display", "测试输出")
        ]
        
        print("📋 测试台内容检查:")
        all_passed = True
        for check, desc in checks:
            if check in content:
                print(f"   ✅ {desc}")
            else:
                print(f"   ❌ {desc} - 未找到: {check}")
                all_passed = False
        
        # 显示文件统计
        lines = content.count('\n')
        print(f"📊 测试台统计: {lines} 行代码")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 读取测试台失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🎯 开始Counter TDD完整测试")
    print("="*60)
    print("目标：验证带有完整测试台的TDD流程能否正常工作")
    print("- 使用新创建的counter_8bit_tb.v测试台")
    print("- 触发完整的TDD循环（红→绿→重构）")
    print("- 验证iverilog编译和仿真执行")
    print("- 检查文件保存和结果输出")
    print("="*60)
    
    # 验证测试台
    testbench_ok = await verify_testbench_content()
    
    if not testbench_ok:
        print("⚠️ 测试台验证失败，但继续进行TDD测试")
    
    # 运行TDD测试
    tdd_result = await test_counter_with_testbench()
    
    print("\n" + "="*60)
    print("🎉 Counter TDD测试总结")
    print(f"  测试台验证: {'✅ 通过' if testbench_ok else '⚠️ 部分问题'}")
    print(f"  TDD流程测试: {'✅ 通过' if tdd_result else '❌ 失败'}")
    
    if tdd_result:
        print("\n🎊 Counter TDD测试成功！")
        print("✅ 系统现在应该能够：")
        print("   1. ✅ 识别用户提供的测试台文件")
        print("   2. ✅ 触发完整的TDD循环流程")
        print("   3. ✅ 执行iverilog编译和仿真")
        print("   4. ✅ 正确处理测试失败和迭代修复")
        print("   5. ✅ 保存所有生成的文件和日志")
        print("\n🎯 建议：查看生成的实验目录和仿真输出了解详细结果")
    else:
        print("\n❌ Counter TDD测试失败")
        print("需要进一步调试TDD协调器或测试台兼容性问题")
    
    return tdd_result

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)