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
wire [WIDTH:0] internal_sum;
wire           carry_out;

// 功能实现：16位加法器，包含进位链和溢出检测
assign internal_sum = {1'b0, a} + {1'b0, b} + cin;
assign carry_out = internal_sum[WIDTH];

// 输出赋值
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        sum <= internal_sum[WIDTH-1:0];
        cout <= carry_out;
        
        // 溢出检测：当两个同号操作数相加，结果符号与操作数符号相反时溢出
        // 溢出条件：MSB的进位输入（cin）与进位输出不一致
        // 即：(a[15] == b[15]) && (a[15] != sum[15])
        // 等价于：(a[15] & b[15] & ~sum[15]) | (~a[15] & ~b[15] & sum[15])
        // 但更简单的方式是判断进位输入与进位输出是否不同
        overflow <= (cin ^ carry_out);
    end
end

endmodule