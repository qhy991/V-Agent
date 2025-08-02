#!/usr/bin/env python3
"""
测试TDD系统的错误反馈机制
专门用于验证rst/rst_n端口错误的修复能力
"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions.test_driven_coordinator import TestDrivenCoordinator
from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig

async def test_tdd_error_feedback():
    """测试TDD错误反馈机制"""
    print("🧪 测试TDD系统的错误反馈和修复机制")
    print("=" * 60)
    
    # 初始化配置
    config = FrameworkConfig.from_env()
    
    # 初始化协调器
    coordinator = EnhancedCentralizedCoordinator(config)
    
    # 注册智能体
    verilog_agent = EnhancedRealVerilogAgent(config)
    review_agent = EnhancedRealCodeReviewAgent(config)
    
    coordinator.register_agent(verilog_agent)
    coordinator.register_agent(review_agent)
    
    # 初始化TDD协调器
    tdd_coordinator = TestDrivenCoordinator(coordinator)
    
    # 清晰的设计需求，明确指定rst_n接口
    design_requirements = """
设计一个8位计数器模块counter_8bit，严格按照以下接口规范实现：

**关键要求 - 接口必须完全匹配**:
```verilog
module counter_8bit (
    input        clk,       // 时钟
    input        rst_n,     // 异步复位（低电平有效） - 注意是rst_n不是rst！
    input        enable,    // 计数使能
    input        up_down,   // 计数方向(1:上计数, 0:下计数)
    output [7:0] count,     // 计数值
    output       overflow   // 溢出标志
);
```

**功能要求**:
- 异步复位：当rst_n为低电平时，count=0, overflow=0
- 同步计数：在时钟上升沿进行计数
- 使能控制：enable为高时计数，为低时保持
- 双向计数：up_down=1上计数，up_down=0下计数
- 溢出检测：上计数255→0时overflow=1，下计数0→255时overflow=1

**警告**：
1. 端口名必须是rst_n，不能是rst！
2. 复位逻辑必须是negedge rst_n，不能是negedge rst！
3. 复位条件必须是if (!rst_n)，不能是if (!rst)！
"""
    
    # 指定现有的测试台路径
    testbench_path = "/home/haiyan/Research/CentralizedAgentFramework/test_cases/counter_8bit_tb.v"
    
    # 验证测试台存在
    if not os.path.exists(testbench_path):
        print(f"❌ 测试台文件不存在: {testbench_path}")
        return False
    
    print(f"✅ 使用测试台: {testbench_path}")
    print(f"🎯 设计需求: Counter 8-bit with strict rst_n interface")
    
    try:
        # 执行TDD循环，限制迭代次数避免无限循环
        # 设置TDD配置
        tdd_coordinator.config.max_iterations = 3  # 减少迭代次数，专注于错误修复验证
        
        result = await tdd_coordinator.execute_test_driven_task(
            task_description=design_requirements,
            testbench_path=testbench_path
        )
        
        print("\n" + "=" * 60)
        print("📊 TDD错误反馈测试结果")
        print("=" * 60)
        
        if result.get("success", False):
            print("✅ TDD流程成功完成")
            print(f"📈 总迭代次数: {result.get('iterations_completed', 0)}")
            print(f"⏱️ 总耗时: {result.get('total_duration', 0):.2f} 秒")
            
            # 检查最终生成的文件是否修复了rst_n问题
            if "final_design_files" in result:
                print("\n🔍 检查最终生成的设计文件:")
                for file_path in result["final_design_files"]:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if "input rst_n" in content and "negedge rst_n" in content:
                                print(f"✅ {file_path}: rst_n接口正确")
                            elif "input rst" in content:
                                print(f"❌ {file_path}: 仍然使用错误的rst接口")
                            else:
                                print(f"⚠️ {file_path}: 无法确定接口类型")
                        
            return True
        else:
            print("❌ TDD流程失败")
            error_msg = result.get("error", "未知错误")
            print(f"❌ 失败原因: {error_msg}")
            
            # 检查是否存在错误反馈信息
            if "iteration_results" in result:
                print("\n🔍 迭代过程分析:")
                for i, iteration in enumerate(result["iteration_results"], 1):
                    print(f"第{i}次迭代:")
                    if "compilation_errors" in iteration:
                        print(f"  编译错误: {iteration['compilation_errors'][:200]}...")
                    if "improvement_suggestions" in iteration:
                        print(f"  改进建议: {len(iteration['improvement_suggestions'])} 条")
            
            return False
            
    except Exception as e:
        print(f"❌ TDD测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tdd_error_feedback())
    if success:
        print("\n🎉 TDD错误反馈机制测试成功")
        sys.exit(0)
    else:
        print("\n💥 TDD错误反馈机制测试失败")
        sys.exit(1)