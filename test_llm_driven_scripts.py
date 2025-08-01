#!/usr/bin/env python3
"""
测试真实的LLM驱动脚本生成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import FrameworkConfig
from agents.real_code_reviewer import RealCodeReviewAgent
import time


async def test_llm_driven_script_generation():
    """测试真实的LLM驱动脚本生成"""
    print("🧠 测试LLM驱动的脚本生成...")
    
    config = FrameworkConfig.from_env()
    agent = RealCodeReviewAgent(config)
    
    # 创建一个需要LLM分析的复杂场景
    test_dir = Path("llm_test_project")
    test_dir.mkdir(exist_ok=True)
    
    # 创建一个复杂的Verilog设计
    complex_design = test_dir / "complex_design.v"
    design_content = '''
module complex_processor (
    input wire clk,
    input wire reset,
    input wire [31:0] instruction_input,
    input wire [31:0] data_input,
    output reg [31:0] result_output,
    output reg operation_complete,
    output reg error_flag
);

// 复杂的状态机
reg [3:0] state;
reg [31:0] accumulator;
reg [31:0] memory [0:255];

localparam IDLE = 4'b0000;
localparam FETCH = 4'b0001;
localparam DECODE = 4'b0010;
localparam EXECUTE = 4'b0011;
localparam STORE = 4'b0100;

always @(posedge clk or posedge reset) begin
    if (reset) begin
        state <= IDLE;
        accumulator <= 32'b0;
        result_output <= 32'b0;
        operation_complete <= 1'b0;
        error_flag <= 1'b0;
    end else begin
        case (state)
            IDLE: begin
                if (instruction_input != 32'b0) begin
                    state <= FETCH;
                end
            end
            FETCH: state <= DECODE;
            DECODE: begin
                case (instruction_input[31:28])
                    4'b0001: state <= EXECUTE; // ADD
                    4'b0010: state <= EXECUTE; // SUB
                    4'b0011: state <= EXECUTE; // MUL
                    default: begin
                        error_flag <= 1'b1;
                        state <= IDLE;
                    end
                endcase
            end
            EXECUTE: begin
                case (instruction_input[31:28])
                    4'b0001: accumulator <= accumulator + data_input;
                    4'b0010: accumulator <= accumulator - data_input;
                    4'b0011: accumulator <= accumulator * data_input;
                endcase
                state <= STORE;
            end
            STORE: begin
                result_output <= accumulator;
                operation_complete <= 1'b1;
                state <= IDLE;
            end
            default: state <= IDLE;
        endcase
    end
end

endmodule
'''
    complex_design.write_text(design_content)
    
    print(f"📁 创建复杂设计: {complex_design}")
    
    # 测试1: 使用Function Calling让LLM决定如何构建项目
    start_time = time.time()
    
    print("\n🎯 让LLM分析并决定构建策略...")
    
    # 使用智能体的完整处理流程，让LLM分析项目需求
    user_request = f"""
    我有一个复杂的处理器设计文件: {complex_design}
    
    请分析这个设计的特点，然后：
    1. 判断是否需要测试台
    2. 选择合适的构建策略（makefile还是bash）
    3. 考虑这个设计的特殊需求
    4. 生成相应的构建脚本
    
    设计包含：复杂状态机、内存数组、多种运算类型
    """
    
    response = await agent.process_with_function_calling(
        user_request=user_request,
        max_iterations=3
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️  LLM处理时间: {duration:.2f} 秒")
    print(f"📊 响应长度: {len(str(response))} 字符")
    
    # 测试2: 直接工具调用 vs LLM驱动对比
    print("\n⚡ 对比测试:")
    
    # 硬编码模板（快速）
    template_start = time.time()
    from tools.script_tools import ScriptManager
    script_manager = ScriptManager()
    
    template_script = script_manager.generate_build_script(
        verilog_files=[str(complex_design)],
        testbench_files=[],
        target_name="complex_sim",
        include_wave_generation=True
    )
    
    template_end = time.time()
    template_duration = template_end - template_start
    
    print(f"   硬编码模板: {template_duration:.3f} 秒")
    print(f"   LLM驱动: {duration:.2f} 秒")
    
    return duration > 1.0  # 检查是否超过1秒


if __name__ == "__main__":
    asyncio.run(test_llm_driven_script_generation())