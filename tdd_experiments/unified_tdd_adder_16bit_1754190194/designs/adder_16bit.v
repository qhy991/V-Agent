module adder_16bit #(
    parameter WIDTH = 16
) (
    input               clk,
    input               rst,
    input  [WIDTH-1:0]  a,
    input  [WIDTH-1:0]  b,
    input               cin,
    output logic [WIDTH-1:0] sum,
    output logic        cout,
    output logic        overflow
);

// 内部信号声明
logic [WIDTH:0] result;  // 用于计算进位的扩展结果，包含额外的进位位

// 功能实现：16位二进制加法器（纯组合逻辑）
assign result = {1'b0, a} + {1'b0, b} + cin;

// 输出赋值
assign sum    = result[WIDTH-1:0];
assign cout   = result[WIDTH];
assign overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != result[WIDTH-1]);

endmodule