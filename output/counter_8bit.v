```verilog
/*
 * Module: counter_8bit_up_down
 *
 * Description:
 * 8位可向上/向下计数的计数器，支持使能信号和异步复位。
 * 当使能信号有效时，根据方向控制信号进行加法或减法计数；
 * 复位信号异步清除计数值为0。
 *
 * Parameters:
 *   WIDTH - 计数器位宽 (默认为8)
 *
 * Input Ports:
 *   clk       - 时钟输入
 *   en        - 使能信号，控制计数是否生效
 *   up_down   - 方向控制信号，1表示向上计数，0表示向下计数
 *   rst_n     - 异步复位信号，低电平有效
 *
 * Output Ports:
 *   count     - 当前计数值输出 (8位)
 *
 * Special Features:
 *   - 异步复位功能
 *   - 方向可控计数
 *
 * Timing Constraints:
 *   目标频率通常为50MHz至100MHz
 *
 * Area Constraints:
 *   尽量优化逻辑门数量以减少面积
 *
 * Power Considerations:
 *   在静态条件下功耗较低，动态功耗取决于时钟频率和计数器活动性
 */

`timescale 1ns / 1ps

module counter_8bit_up_down #(
    parameter int WIDTH = 8
) (
    input      clk,
    input      en,
    input      up_down,
    input      rst_n,
    output reg [WIDTH-1:0] count
);

// Internal signals
reg [WIDTH-1:0] next_count;

// Module documentation
// This is a 8-bit up/down counter with enable and asynchronous reset.
// It increments or decrements based on the up_down signal when enabled.

// Main logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Asynchronous reset: set count to 0
        count <= {WIDTH{1'b0}};
    end else if (en) begin
        // Only update count when enabled
        if (up_down) begin
            // Up counting
            next_count <= count + 1;
        end else begin
            // Down counting
            next_count <= count - 1;
        end
        count <= next_count;
    end
end

// Boundary check for overflow/underflow (optional, can be removed for area optimization)
// This is a simple check that can be used for debugging or verification
// In industrial designs, this may be omitted for performance reasons
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Reset condition
    end else if (en) begin
        // Check for overflow (max value)
        if (up_down && (count == {WIDTH{1'b1}})) begin
            // Overflow detected
            // Can add alert or logging here if needed
        end
        // Check for underflow (min value)
        if (!up_down && (count == {WIDTH{1'b0}})) begin
            // Underflow detected
            // Can add alert or logging here if needed
        end
    end
end

endmodule
```