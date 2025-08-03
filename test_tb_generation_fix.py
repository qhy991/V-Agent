#!/usr/bin/env python3
"""
测试测试台生成修复效果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent

async def test_testbench_generation():
    """测试测试台生成功能"""
    print("🧪 测试测试台生成修复效果")
    print("=" * 60)
    
    # 创建代理实例
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    # 测试用的Verilog代码
    test_verilog_code = """
module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    // 16位行波进位加法器
    wire [16:0] carry;
    assign carry[0] = cin;
    
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : full_adder_stage
            assign sum[i] = a[i] ^ b[i] ^ carry[i];
            assign carry[i+1] = (a[i] & b[i]) | (carry[i] & (a[i] ^ b[i]));
        end
    endgenerate
    
    assign cout = carry[16];
    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);

endmodule
"""
    
    print("📝 生成测试台...")
    
    try:
        # 调用测试台生成工具
        result = await agent._tool_generate_testbench(
            module_name="adder_16bit",
            verilog_code=test_verilog_code,
            test_scenarios=["basic functionality test", "carry propagation test"],
            clock_period=10.0,
            simulation_time=1000
        )
        
        if result.get("success", False):
            print("✅ 测试台生成成功！")
            print(f"📁 文件路径: {result.get('file_path', 'N/A')}")
            print(f"🆔 文件ID: {result.get('file_id', 'N/A')}")
            
            # 显示生成的代码前20行
            testbench_code = result.get("testbench_code", "")
            print(f"\n📋 生成的测试台代码前20行:")
            print("-" * 40)
            lines = testbench_code.split('\n')[:20]
            for i, line in enumerate(lines, 1):
                print(f"{i:2d}: {line}")
            
            # 检查是否包含Markdown格式
            markdown_indicators = ['##', '---', '###', '**', '```', '---', '===']
            markdown_count = sum(1 for indicator in markdown_indicators if indicator in testbench_code)
            
            print(f"\n🔍 代码质量检查:")
            print(f"   代码长度: {len(testbench_code)} 字符")
            print(f"   Markdown标记数量: {markdown_count}")
            print(f"   是否以`timescale开头: {testbench_code.strip().startswith('`timescale')}")
            print(f"   是否以endmodule结尾: {testbench_code.strip().endswith('endmodule')}")
            
            if markdown_count == 0 and testbench_code.strip().startswith('`timescale'):
                print("✅ 代码格式正确 - 没有Markdown格式，是纯Verilog代码")
            else:
                print("⚠️ 代码格式有问题 - 可能包含Markdown格式或格式不正确")
                
        else:
            print(f"❌ 测试台生成失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_testbench_generation()) 