#!/usr/bin/env python3
"""
测试新的错误处理机制
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig


async def test_error_classification():
    """测试错误分类功能"""
    print("🧪 测试错误分类功能...")
    
    agent = EnhancedRealCodeReviewAgent()
    
    # 测试不同类型的错误
    test_errors = [
        {
            "message": "file_workspace/testbenches/testbench_counter.v:76: syntax error",
            "expected_type": "compilation_syntax"
        },
        {
            "message": "module not found: counter",
            "expected_type": "compilation_semantic"
        },
        {
            "message": "simulation timeout after 1000ns",
            "expected_type": "simulation_runtime"
        },
        {
            "message": "no space left on device",
            "expected_type": "system_resource"
        }
    ]
    
    for test_case in test_errors:
        error_info = agent._classify_simulation_error(test_case["message"])
        print(f"📋 错误信息: {test_case['message']}")
        print(f"🔍 分类结果: {error_info['error_type']}")
        print(f"🎯 期望类型: {test_case['expected_type']}")
        print(f"✅ 分类正确: {error_info['error_type'] == test_case['expected_type']}")
        print(f"📊 严重程度: {error_info['severity']}")
        print(f"🔧 修复优先级: {error_info['fix_priority']}")
        print("---")


async def test_error_enhancement():
    """测试错误信息增强功能"""
    print("\n🧪 测试错误信息增强功能...")
    
    agent = EnhancedRealCodeReviewAgent()
    
    error_message = "file_workspace/testbenches/testbench_counter.v:76: syntax error"
    error_context = {
        "file_paths": ["counter.v", "testbench_counter.v"],
        "stage": "compilation",
        "simulator": "iverilog",
        "command": "iverilog -o simulation counter.v testbench_counter.v",
        "working_directory": "/tmp/test"
    }
    
    simulation_result = {
        "success": False,
        "stage": "compilation",
        "return_code": 10,
        "compilation_output": "syntax error in line 76",
        "error_output": "Syntax in assignment statement l-value"
    }
    
    enhanced_error = agent._enhance_error_information(
        error_message=error_message,
        error_context=error_context,
        simulation_result=simulation_result
    )
    
    print(f"📋 原始错误: {error_message}")
    print(f"🔍 增强错误信息:")
    print(f"  - 错误类型: {enhanced_error['error_classification']['error_type']}")
    print(f"  - 严重程度: {enhanced_error['error_classification']['severity']}")
    print(f"  - 修复建议数量: {len(enhanced_error['recovery_suggestions'])}")
    print(f"  - 调试步骤数量: {len(enhanced_error['debug_information']['suggested_debug_steps'])}")
    print(f"  - 上下文信息: {len(enhanced_error['context_information'])} 项")
    print(f"  - 技术细节: {len(enhanced_error['technical_details'])} 项")


async def test_error_prompt_generation():
    """测试错误prompt生成功能"""
    print("\n🧪 测试错误prompt生成功能...")
    
    agent = EnhancedRealCodeReviewAgent()
    
    # 创建增强错误信息
    enhanced_error = {
        "original_error": "file_workspace/testbenches/testbench_counter.v:76: syntax error",
        "error_classification": {
            "error_type": "compilation_syntax",
            "severity": "high",
            "category": "compilation",
            "fix_priority": "high",
            "detailed_analysis": {
                "issue": "语法错误导致编译失败",
                "common_causes": ["缺少分号", "端口连接错误", "信号类型不匹配"],
                "fix_strategy": "逐行检查语法，重点关注错误行及其上下文"
            }
        },
        "context_information": {
            "compilation_stage": "compilation",
            "simulator_info": "iverilog",
            "working_directory": "/tmp/test"
        },
        "technical_details": {
            "success": False,
            "return_code": 10,
            "error_output": "Syntax in assignment statement l-value"
        },
        "recovery_suggestions": [
            "立即检查错误行及其前后几行的语法",
            "验证所有信号声明和端口定义"
        ],
        "debug_information": {
            "suggested_debug_steps": [
                "查看完整的编译/仿真输出",
                "检查相关文件的语法"
            ]
        }
    }
    
    design_code = """
module counter(
    input wire clk,
    input wire reset,
    input wire enable,
    output reg [7:0] count
);
    always @(posedge clk or posedge reset) begin
        if (reset)
            count <= 8'b0;
        else if (enable)
            count <= count + 1;
    end
endmodule
"""
    
    testbench_code = """
module testbench_counter;
    reg clk, reset, enable;
    wire [7:0] count;
    
    counter dut(clk, reset, enable, count);
    
    initial begin
        clk = 0;
        reset = 1;
        enable = 0;
        #10 reset = 0;
        #10 enable = 1;
        #1000 $finish;
    end
    
    always #5 clk = ~clk;
endmodule
"""
    
    error_prompt = agent._generate_simulation_error_prompt(
        enhanced_error=enhanced_error,
        design_code=design_code,
        testbench_code=testbench_code
    )
    
    print(f"📝 生成的错误prompt长度: {len(error_prompt)} 字符")
    print(f"🔍 Prompt包含的关键信息:")
    print(f"  - 错误分类信息: {'✅' if '错误分类信息' in error_prompt else '❌'}")
    print(f"  - 错误详情: {'✅' if '错误详情' in error_prompt else '❌'}")
    print(f"  - 上下文信息: {'✅' if '上下文信息' in error_prompt else '❌'}")
    print(f"  - 技术细节: {'✅' if '技术细节' in error_prompt else '❌'}")
    print(f"  - 修复建议: {'✅' if '建议的修复行动' in error_prompt else '❌'}")
    print(f"  - 调试指导: {'✅' if '调试指导' in error_prompt else '❌'}")
    print(f"  - 设计代码: {'✅' if '设计代码' in error_prompt else '❌'}")
    print(f"  - 测试台代码: {'✅' if '测试台代码' in error_prompt else '❌'}")
    
    # 显示prompt的前500个字符
    print(f"\n📄 Prompt预览 (前500字符):")
    print(error_prompt[:500] + "...")


async def main():
    """主测试函数"""
    print("🚀 开始测试新的错误处理机制...")
    print("=" * 60)
    
    try:
        await test_error_classification()
        await test_error_enhancement()
        await test_error_prompt_generation()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 