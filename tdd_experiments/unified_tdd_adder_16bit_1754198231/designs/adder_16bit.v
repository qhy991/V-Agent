module adder_16bit #(
    parameter WIDTH = 16
) (
    input           clk,
    input           rst,
    input  [WIDTH-1:0] a,
    input  [WIDTH-1:0] b,
    input           cin,
    output reg [WIDTH-1:0] sum,
    output reg      cout,
    output reg      overflow
);

// 内部信号声明
wire [WIDTH-1:0] internal_sum;
wire             internal_cout;
wire             internal_overflow;

// 组合逻辑实现16位加法器
assign {internal_cout, internal_sum} = {1'b0, a} + {1'b0, b} + cin;

// 有符号溢出检测：当两个同号操作数相加结果符号相反时发生溢出
// a[15] 和 b[15] 是符号位，internal_sum[15] 是结果符号位
assign internal_overflow = (a[15] == b[15]) && (a[15] != internal_sum[15]);

// 同步寄存器输出
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        sum <= internal_sum;
        cout <= internal_cout;
        overflow <= internal_overflow;
    end
end

endmodule