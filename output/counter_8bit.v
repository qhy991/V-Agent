```verilog
/*
 * Module: counter_8bit
 *
 * Description:
 * 8位可向上或向下计数的计数器，支持使能信号和异步复位。
 * 当使能为高时，根据方向控制信号进行加法或减法计数；
 * 当使能为低时，计数器保持当前状态。
 *
 * Parameters:
 *   WIDTH - 计数器位宽（默认8位）
 *
 * Input Ports:
 *   clk        - 时钟输入 (1-bit)
 *   rst_n      - 异步复位信号 (1-bit, 低电平有效)
 *   en         - 使能信号 (1-bit, 高电平有效)
 *   up_down    - 方向控制信号 (1-bit, 1为向上计数，0为向下计数)
 *
 * Output Ports:
 *   count      - 8位计数值输出 (8-bit)
 *
 * Special Features:
 *   - 异步复位功能
 *   - 方向控制
 *   - 使能控制
 *
 * Timing Constraints:
 *   - 时钟频率需满足设计要求（如50MHz或更高）
 *
 * Area Constraints:
 *   - 尽量优化逻辑门数量以减少面积
 *
 * Power Considerations:
 *   - 在静态状态下应尽可能降低功耗
 *
 * Design Notes:
 *   - 使用标准Verilog-2001/SystemVerilog语法
 *   - 采用清晰的模块化架构
 *   - 包含详细的注释和模块文档
 *   - 添加适当的断言和检查
 */

`timescale 1ns / 1ps

module counter_8bit #(
    parameter int WIDTH = 8  // 计数器位宽
)(
    input  logic clk,
    input  logic rst_n,
    input  logic en,
    input  logic up_down,
    output logic [WIDTH-1:0] count
);

    // 内部信号声明
    logic [WIDTH-1:0] count_reg;

    // 模块功能描述
    // 该计数器在时钟上升沿触发，根据使能信号和方向控制信号进行计数
    // 当复位信号有效时，计数器被清零
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // 异步复位：将计数器清零
            count_reg <= '0;
        end else if (en) begin
            // 使能有效时，根据方向控制信号进行加法或减法计数
            if (up_down) begin
                // 向上计数
                count_reg <= count_reg + 1;
            end else begin
                // 向下计数
                count_reg <= count_reg - 1;
            end
        end
    end

    // 输出计数值
    assign count = count_reg;

    // 断言检查：确保计数器位宽为正整数
    `ifndef SYNTHESIS
    initial begin
        assert(WIDTH > 0) else $fatal("Counter width must be greater than 0");
    end
    `endif

endmodule
```