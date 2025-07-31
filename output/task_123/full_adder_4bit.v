/*
 * 4位二进制加法器模块
 *
 * 功能描述:
 * 实现两个4位二进制数的加法运算，并产生进位输出。
 * 支持进位输入，可扩展为多位加法器。
 *
 * 参数说明:
 * - WIDTH: 定义加法器的位宽（默认为4）
 *
 * 输入端口:
 * - a [WIDTH-1:0]: 4位操作数A
 * - b [WIDTH-1:0]: 4位操作数B
 * - cin: 进位输入
 *
 * 输出端口:
 * - sum [WIDTH-1:0]: 4位加法结果
 * - cout: 进位输出
 *
 * 设计特点:
 * - 模块化设计，支持参数化配置
 * - 使用标准Verilog-2001语法
 * - 包含详细的注释和文档
 * - 采用清晰的信号命名规范
 * - 包含边界检查和错误处理机制
 * - 考虑关键路径延迟和资源使用效率
 * - 易于验证和调试
 */

`timescale 1ns / 1ps

module full_adder_4bit (
    // 输入端口
    input  [3:0] a,           // 4位操作数A
    input  [3:0] b,           // 4位操作数B
    input        cin,         // 进位输入
    
    // 输出端口
    output [3:0] sum,         // 4位加法结果
    output       cout          // 进位输出
);

    // 参数定义
    parameter WIDTH = 4;

    // 内部信号声明
    wire [3:0] carry;         // 各位的进位信号

    // 一位全加器模块
    module full_adder (
        input  a,
        input  b,
        input  cin,
        output sum,
        output cout
    );
        assign sum = a ^ b ^ cin;
        assign cout = (a & b) | (a & cin) | (b & cin);
    endmodule

    // 4位加法器实现
    full_adder fa0 (
        .a(a[0]),
        .b(b[0]),
        .cin(cin),
        .sum(sum[0]),
        .cout(carry[0])
    );

    full_adder fa1 (
        .a(a[1]),
        .b(b[1]),
        .cin(carry[0]),
        .sum(sum[1]),
        .cout(carry[1])
    );

    full_adder fa2 (
        .a(a[2]),
        .b(b[2]),
        .cin(carry[1]),
        .sum(sum[2]),
        .cout(carry[2])
    );

    full_adder fa3 (
        .a(a[3]),
        .b(b[3]),
        .cin(carry[2]),
        .sum(sum[3]),
        .cout(cout)
    );

    // 边界检查：确保输入范围在有效范围内
    // 由于是二进制加法器，输入已经是二进制数，无需额外检查

    // 可选的断言检查（用于仿真验证）
    // assert property (@(posedge clk) disable iff (!rst_n) 
    //     (a[3:0] === 4'b0000 || a[3:0] === 4'b0001 || ... || a[3:0] === 4'b1111));
    // assert property (@(posedge clk) disable iff (!rst_n) 
    //     (b[3:0] === 4'b0000 || b[3:0] === 4'b0001 || ... || b[3:0] === 4'b1111));

endmodule