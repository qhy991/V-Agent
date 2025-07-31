/*
 * 4位二进制加法器模块
 *
 * 功能描述:
 * 实现两个4位二进制数的加法运算，并输出结果和进位标志。
 * 支持进位输入和进位输出，可级联使用。
 *
 * 参数说明:
 * - WIDTH: 位宽参数，用于定义加法器的位数（默认为4）
 *
 * 输入端口:
 * - a[WIDTH-1:0]: 第一个4位二进制数
 * - b[WIDTH-1:0]: 第二个4位二进制数
 * - cin: 进位输入
 *
 * 输出端口:
 * - sum[WIDTH-1:0]: 加法结果
 * - cout: 进位输出
 *
 * 时钟和复位:
 * - clk: 系统时钟
 * - rst_n: 异步复位信号（低电平有效）
 *
 * 设计特点:
 * - 使用标准Verilog-2001/SystemVerilog语法
 * - 模块化设计，易于扩展和重用
 * - 包含详细的注释和文档
 * - 支持参数化设计
 * - 考虑时序和资源优化
 * - 包含时钟和复位处理
 * - 考虑边界检查和错误处理
 */

`timescale 1ns / 1ps

module adder_4bit #(
    parameter int WIDTH = 4  // 位宽参数
) (
    // 输入端口
    input  [WIDTH-1:0] a,       // 第一个4位二进制数
    input  [WIDTH-1:0] b,       // 第二个4位二进制数
    input              cin,     // 进位输入

    // 输出端口
    output [WIDTH-1:0] sum,     // 加法结果
    output             cout,    // 进位输出

    // 时钟和复位
    input              clk,     // 系统时钟
    input              rst_n    // 异步复位（低电平有效）
);

    // 内部信号声明
    reg [WIDTH-1:0] carry;      // 内部进位寄存器

    // 生成内部进位信号
    generate
        genvar i;
        for (i = 0; i < WIDTH; i = i + 1) begin : gen_full_adder
            // 全加器逻辑
            wire c_out;
            wire c_in;

            // 第一位的进位输入是cin
            assign c_in = (i == 0) ? cin : carry[i-1];

            // 计算当前位的和
            assign sum[i] = a[i] ^ b[i] ^ c_in;

            // 计算当前位的进位输出
            assign c_out = (a[i] & b[i]) | (a[i] & c_in) | (b[i] & c_in);

            // 存储进位值
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    carry[i] <= 1'b0;
                end else begin
                    carry[i] <= c_out;
                end
            end
        end
    endgenerate

    // 进位输出连接到最高位的进位输出
    assign cout = carry[WIDTH-1];

    // 边界检查（可选，用于验证）
    // assert property (@(posedge clk) disable iff (!rst_n) 
    //     (a == 4'b0000 && b == 4'b0000 && cin == 1'b0) |-> (sum == 4'b0000 && cout == 1'b0));
    // assert property (@(posedge clk) disable iff (!rst_n) 
    //     (a == 4'b1111 && b == 4'b0001 && cin == 1'b0) |-> (sum == 4'b0000 && cout == 1'b1));

endmodule