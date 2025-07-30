```verilog
/*
 * Module Name: counter_8bit
 *
 * Description:
 * 8位可向上/向下计数的计数器，支持使能信号控制计数操作，并具有异步复位功能。
 * 当使能信号有效时，根据方向信号进行加1或减1操作；异步复位将计数器清零。
 *
 * Parameters:
 *   WIDTH - 计数器位宽 (默认为8)
 *
 * Input Ports:
 *   clk       - 时钟输入
 *   en        - 使能信号，控制计数是否进行
 *   up_down   - 方向控制信号，1表示向上计数，0表示向下计数
 *   rst_n     - 异步复位信号，低电平有效
 *
 * Output Ports:
 *   count     - 当前计数值输出
 *
 * Special Features:
 *   - 异步复位
 *   - 方向控制
 *   - 使能控制
 *
 * Timing Constraints:
 *   时钟频率应满足FPGA器件的时序要求，通常为50MHz至200MHz之间
 *
 * Area Constraints:
 *   尽量优化逻辑资源使用，避免过多LUT和FF占用
 *
 * Power Considerations:
 *   在使能无效时，计数器不进行操作，以降低动态功耗
 */

`timescale 1ns / 1ps

module counter_8bit #(
    parameter int WIDTH = 8
) (
    input  wire              clk,
    input  wire              en,
    input  wire              up_down,
    input  wire              rst_n,
    output reg [WIDTH-1:0]   count
);

    // 内部信号声明
    reg [WIDTH-1:0]          next_count;

    // 模块功能描述
    // 该模块实现一个8位可向上/向下计数的计数器，支持使能信号控制计数操作，并具有异步复位功能。
    // 当使能信号有效时，根据方向信号进行加1或减1操作；异步复位将计数器清零。

    // 异步复位处理
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};  // 异步复位，清零计数器
        end else if (en) begin
            // 根据方向信号进行加法或减法操作
            if (up_down) begin
                // 向上计数
                next_count <= count + 1;
            end else begin
                // 向下计数
                next_count <= count - 1;
            end
            count <= next_count;
        end
    end

    // 边界检查：确保计数器在0到2^WIDTH-1范围内循环
    // 注意：对于有符号计数器，可能需要不同的处理方式
    // 这里我们假设是无符号计数器
    // 当向上计数超过最大值时，自动回绕到0
    // 当向下计数低于0时，自动回绕到最大值
    // 由于Verilog中加减法会自动处理溢出，因此不需要显式处理

    // 可选的断言（用于仿真验证）
    // `ifdef SIMULATION
    //     assert property (@(posedge clk) disable iff (!en) (count == next_count)) 
    //         else $error("Count not updated when enable is active");
    // `endif

endmodule
```