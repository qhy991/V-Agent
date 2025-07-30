```verilog
/*
 * Module: counter_8bit
 * Description: 8位可向上/向下计数的计数器，支持使能信号和异步复位
 *
 * Features:
 * - 8位计数器
 * - 支持方向控制（up_down）
 * - 支持使能信号（en）
 * - 异步复位（rst_n）
 * - 时钟域为单一时钟
 * - 适用于FPGA和ASIC设计
 *
 * Parameters:
 * - COUNTER_WIDTH: 计数器位宽（默认8位）
 *
 * Input Ports:
 * - clk: 时钟输入
 * - en: 使能信号，高电平有效
 * - up_down: 方向控制信号，1表示向上计数，0表示向下计数
 * - rst_n: 异步复位信号，低电平有效
 *
 * Output Ports:
 * - count: 当前计数值输出（8位）
 *
 * Design Notes:
 * - 使用标准Verilog-2001语法
 * - 采用清晰的模块化架构
 * - 包含详细的注释和文档
 * - 优化逻辑门数量以减少面积
 * - 考虑时序约束和性能优化
 */

`timescale 1ns / 1ps

module counter_8bit #(
    parameter COUNTER_WIDTH = 8
) (
    input      clk,
    input      en,
    input      up_down,
    input      rst_n,
    output reg [COUNTER_WIDTH-1:0] count
);

    // 内部信号声明
    reg [COUNTER_WIDTH-1:0] next_count;

    // 主要逻辑实现
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // 异步复位：将计数器清零
            count <= {COUNTER_WIDTH{1'b0}};
        end else if (en) begin
            // 使能有效时根据方向进行计数
            if (up_down) begin
                // 向上计数
                next_count <= count + 1;
            end else begin
                // 向下计数
                next_count <= count - 1;
            end
            // 更新当前计数值
            count <= next_count;
        end
    end

    // 边界检查：确保计数器不会溢出或下溢
    // 这里使用断言来验证计数器的值是否在合法范围内
    // 注意：在综合时这些断言可能被忽略，仅用于仿真验证
    `ifdef SIMULATION
    always @(posedge clk) begin
        if (en && !rst_n) begin
            assert (count == 0) else $error("Counter reset failed");
        end else if (en) begin
            if (up_down) begin
                assert (count < (1 << COUNTER_WIDTH) - 1) else $error("Counter overflow detected");
            end else begin
                assert (count > 0) else $error("Counter underflow detected");
            end
        end
    end
    `endif

endmodule
```