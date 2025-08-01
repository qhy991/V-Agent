#!/usr/bin/env python3
"""
增强的Agent脚本执行和错误处理能力测试
Enhanced Agent Script Execution and Error Handling Test
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


async def test_enhanced_error_handling():
    """测试增强的错误处理能力"""
    print("🤖 增强的Agent错误处理和迭代能力测试")
    print("=" * 60)
    
    # 初始化增强日志系统
    log_session = setup_enhanced_logging("enhanced_execution_test")
    print(f"📁 实验目录: {log_session.session_log_dir}")
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 创建测试目录
    test_dir = Path("enhanced_execution_test")
    test_dir.mkdir(exist_ok=True)
    
    # 测试1: 语法错误修复测试
    print("\n🎯 测试1: 语法错误自动修复")
    print("-" * 40)
    
    # 创建有语法错误的Verilog文件
    error_file = test_dir / "syntax_error.v"
    error_file.write_text('''
module syntax_error(input clk, output reg [7:0] count);
    always @(posedge clk) begin
        count <= count + 1
        // 缺少分号，这是一个语法错误
    end
endmodule
''')
    
    # 创建测试台
    tb_file = test_dir / "syntax_error_tb.v"
    tb_file.write_text('''
module syntax_error_tb;
    reg clk;
    wire [7:0] count;
    
    syntax_error uut (.clk(clk), .count(count));
    
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    initial begin
        #100 $finish;
    end
endmodule
''')
    
    # 使用Function Calling让智能体处理错误并修复
    task_request = f"""
请处理以下Verilog项目的构建和错误修复：

1. 首先读取文件：{error_file} 和 {tb_file}
2. 生成构建脚本并尝试编译
3. 如果编译失败，请：
   - 分析错误信息
   - 修复源代码中的问题
   - 重新生成构建脚本
   - 再次尝试编译和仿真
4. 重复步骤3直到成功或达到最大尝试次数

要求：展示完整的错误诊断和修复过程
"""
    
    start_time = time.time()
    result = await agent.process_with_function_calling(
        user_request=task_request,
        max_iterations=8  # 增加迭代次数以支持错误修复
    )
    execution_time = time.time() - start_time
    
    print(f"⏱️ 执行时间: {execution_time:.2f}秒")
    print(f"📝 响应摘要:")
    print(result[:500] + "..." if len(result) > 500 else result)
    
    # 测试2: 文件不存在错误恢复
    print("\n🎯 测试2: 文件不存在错误恢复")
    print("-" * 40)
    
    missing_file_task = f"""
请尝试构建一个不存在的Verilog项目：

1. 尝试读取文件：non_existent.v 和 non_existent_tb.v
2. 当发现文件不存在时，请：
   - 创建一个简单的演示模块 (一个8位计数器)
   - 创建相应的测试台
   - 生成构建脚本
   - 执行编译和仿真

要求：展示从"文件不存在"错误中的完整恢复过程
"""
    
    start_time = time.time()
    result2 = await agent.process_with_function_calling(
        user_request=missing_file_task,
        max_iterations=8
    )
    execution_time2 = time.time() - start_time
    
    print(f"⏱️ 执行时间: {execution_time2:.2f}秒")
    print(f"📝 响应摘要:")
    print(result2[:500] + "..." if len(result2) > 500 else result2)
    
    # 测试3: 脚本执行错误和路径修复
    print("\n🎯 测试3: 脚本执行错误和路径修复")
    print("-" * 40)
    
    # 创建一个正确的模块但路径配置错误的情况
    good_module = test_dir / "good_module.v"
    good_module.write_text('''
module good_module(input clk, input rst, output reg [3:0] counter);
    always @(posedge clk or posedge rst) begin
        if (rst)
            counter <= 4'b0000;
        else
            counter <= counter + 1;
    end
endmodule
''')
    
    path_error_task = f"""
请处理以下复杂的构建场景：

1. 读取模块文件：{good_module}
2. 生成一个对应的测试台文件
3. 创建构建脚本，但故意使用错误的文件路径
4. 尝试执行构建脚本
5. 当脚本执行失败时，请：
   - 分析错误原因（路径问题）
   - 修正文件路径配置
   - 重新生成构建脚本
   - 再次执行直到成功

要求：展示路径错误的诊断和修复过程，并最终成功执行仿真
"""
    
    start_time = time.time()
    result3 = await agent.process_with_function_calling(
        user_request=path_error_task,
        max_iterations=10
    )
    execution_time3 = time.time() - start_time
    
    print(f"⏱️ 执行时间: {execution_time3:.2f}秒")
    print(f"📝 响应摘要:")
    print(result3[:500] + "..." if len(result3) > 500 else result3)
    
    # 测试4: 复杂错误链修复
    print("\n🎯 测试4: 复杂错误链修复")
    print("-" * 40)
    
    # 创建包含多种错误的复杂文件
    complex_error_file = test_dir / "complex_error.v"
    complex_error_file.write_text('''
module complex_error(input clk, input [7:0] data_in, output reg [7:0] data_out);
    reg [7:0] internal_reg;
    
    // 错误1: 未声明的信号
    always @(posedge clk) begin
        internal_reg <= data_in + undefined_signal;  // undefined_signal未声明
    end
    
    // 错误2: 语法错误
    always @(posedge clk) begin
        data_out <= internal_reg << 1  // 缺少分号
        if (data_out > 8'hF0) begin  // 语法错误：应该在separate always block
            data_out <= 8'h00;
        end
    end
    
    // 错误3: 端口宽度不匹配
    wire [3:0] narrow_signal;
    assign narrow_signal = data_out;  // 8位赋值给4位
    
endmodule
''')
    
    complex_error_task = f"""
请处理这个包含多种错误的复杂Verilog文件：

文件：{complex_error_file}

这个文件包含多种错误：
1. 未声明的信号
2. 语法错误（缺少分号、不正确的always block结构）
3. 端口宽度不匹配

请按以下步骤处理：
1. 读取并分析文件
2. 尝试生成测试台和构建脚本
3. 执行编译，预期会失败
4. 分析所有编译错误
5. 逐一修复每个错误：
   - 声明缺失的信号
   - 修复语法错误
   - 解决端口宽度问题
6. 为修复后的模块重新生成测试台
7. 重新编译和仿真直到成功

要求：详细展示每个错误的识别、分析和修复过程
"""
    
    start_time = time.time()
    result4 = await agent.process_with_function_calling(
        user_request=complex_error_task,
        max_iterations=12  # 更多迭代以处理复杂错误
    )
    execution_time4 = time.time() - start_time
    
    print(f"⏱️ 执行时间: {execution_time4:.2f}秒")
    print(f"📝 响应摘要:")
    print(result4[:500] + "..." if len(result4) > 500 else result4)
    
    # 总结报告
    print("\n" + "=" * 60)
    print("📊 增强错误处理能力测试总结")
    print("=" * 60)
    
    total_time = execution_time + execution_time2 + execution_time3 + execution_time4
    
    print(f"🕒 总测试时间: {total_time:.2f}秒")
    print(f"📋 测试场景:")
    print(f"  1. 语法错误修复: {execution_time:.2f}秒")
    print(f"  2. 文件不存在恢复: {execution_time2:.2f}秒") 
    print(f"  3. 路径错误修复: {execution_time3:.2f}秒")
    print(f"  4. 复杂错误链修复: {execution_time4:.2f}秒")
    
    # 检查生成的文件
    artifacts_dir = log_session.session_log_dir / "artifacts"
    if artifacts_dir.exists():
        generated_files = list(artifacts_dir.rglob("*"))
        print(f"\n📁 生成的文件: {len(generated_files)} 个")
        for file in generated_files[:10]:  # 只显示前10个
            if file.is_file():
                print(f"   📄 {file.name}")
    
    print("\n✅ 增强错误处理能力测试完成！")
    print(f"📂 详细日志和生成文件位于: {log_session.session_log_dir}")
    
    return True


async def test_iterative_improvement():
    """测试迭代改进能力"""
    print("\n🔬 迭代改进能力专项测试")
    print("=" * 60)
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 创建一个需要多次迭代改进的任务
    iterative_task = """
请设计并实现一个Verilog项目，要求如下：

1. 设计一个16位RISC-V风格的简单CPU核心
2. 包含基本的指令集：ADD, SUB, LOAD, STORE
3. 实现基本的寄存器文件
4. 创建完整的测试台验证所有功能

**重要**：在实现过程中，请：
- 首先创建一个简化版本
- 尝试编译和测试
- 根据测试结果逐步改进和扩展功能
- 如果遇到错误，请分析并修复
- 继续迭代直到实现完整功能

展示完整的迭代开发过程。
"""
    
    start_time = time.time()
    result = await agent.process_with_function_calling(
        user_request=iterative_task,
        max_iterations=15  # 足够的迭代次数支持复杂开发
    )
    execution_time = time.time() - start_time
    
    print(f"⏱️ 迭代开发时间: {execution_time:.2f}秒")
    print(f"📝 迭代过程摘要:")
    
    # 分析响应中的迭代痕迹
    if "tool_calls" in result or "工具调用" in result:
        print("✅ 检测到工具调用活动")
    if "错误" in result or "error" in result.lower():
        print("✅ 检测到错误处理")
    if "修复" in result or "fix" in result.lower():
        print("✅ 检测到修复活动")
    if "重试" in result or "retry" in result.lower():
        print("✅ 检测到重试机制")
    
    print(f"\n📄 完整响应 (前1000字符):")
    print(result[:1000] + "..." if len(result) > 1000 else result)
    
    return True


if __name__ == "__main__":
    async def main():
        try:
            await test_enhanced_error_handling()
            await test_iterative_improvement()
            print("\n🎉 所有测试完成！")
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())