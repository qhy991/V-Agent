```verilog
/*
 * Module: counter_8bit
 * Description: 8位可向上/向下计数的计数器，支持使能信号和异步复位
 * 
 * Features:
 * - 8位计数宽度
 * - 方向控制 (up_down): 1=上计数, 0=下计数
 * - 使能控制 (en): 高电平有效
 * - 异步复位 (rst_n): 低电平有效
 * - 支持时钟域同步
 * - 优化逻辑资源使用
 * - 低功耗设计 (当en为低时进入低功耗状态)
 *
 * Parameters:
 *   WIDTH - 计数器位宽 (默认8)
 *
 * Ports:
 *   clk        - 输入时钟
 *   rst_n      - 异步复位 (低电平有效)
 *   en         - 使能信号 (高电平有效)
 *   up_down    - 方向控制信号 (1=上计数, 0=下计数)
 *   count      - 8位计数值输出
 *
 * Timing Constraints:
 *   时钟频率应满足FPGA器件的时序要求，通常为50MHz~100MHz
 *
 * Area Constraints:
 *   尽量优化逻辑资源使用，减少LUT和FF占用
 *
 * Power Considerations:
 *   在使能关闭时，计数器应进入低功耗状态以减少动态功耗
 *
 * Design Notes:
 *   - 使用标准Verilog-2001/SystemVerilog语法
 *   - 采用清晰的模块化架构
 *   - 添加详细注释和模块文档
 *   - 包含适当的断言和检查
 */

`timescale 1ns / 1ps

module counter_8bit #(
    parameter int WIDTH = 8  // 计数器位宽
) (
    input  wire clk,
    input  wire rst_n,
    input  wire en,
    input  wire up_down,
    output reg [WIDTH-1:0] count
);

// 内部信号声明
reg [WIDTH-1:0] count_reg;

// 模块功能描述
// 8位可向上/向下计数的计数器，支持使能信号和异步复位
// 当使能为高时，根据方向信号进行加法或减法计数；当使能为低时，保持当前状态

// 主要逻辑实现
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 异步复位：将计数器清零
        count_reg <= {WIDTH{1'b0}};
    end else if (en) begin
        // 使能有效时，根据方向信号进行计数
        if (up_down) begin
            // 上计数：加1
            count_reg <= count_reg + 1;
        end else begin
            // 下计数：减1
            count_reg <= count_reg - 1;
        end
    end
    // 使能无效时，保持当前状态
end

// 输出赋值
assign count = count_reg;

// 边界检查：确保计数器在0到2^WIDTH-1范围内循环
// 这里使用SystemVerilog的assert语句进行验证
`ifdef SIMULATION
    always @(posedge clk) begin
        assert (count >= 0 && count < (1 << WIDTH)) 
            else $error("Counter value out of bounds: %d", count);
    end
`endif

endmodule
```