module adder_16bit #(
    parameter WIDTH = 16
) (
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input cin,
    output reg [WIDTH-1:0] sum,
    output reg cout,
    output reg overflow
);

// 内部信号声明
reg [WIDTH:0] internal_sum;  // 用于计算带进位的和，多一位以捕获cout
reg [WIDTH-1:0] temp_sum;
reg temp_cout;

// 功能实现：同步加法器逻辑
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // 计算16位加法，包含输入进位
        internal_sum = {1'b0, a} + {1'b0, b} + cin;
        temp_sum = internal_sum[WIDTH-1:0];
        temp_cout = internal_sum[WIDTH];

        // 更新输出
        sum <= temp_sum;
        cout <= temp_cout;

        // 检测有符号溢出：当两个同号操作数相加结果异号时溢出
        // 同号：a[15] == b[15]
        // 异号：sum[15] != a[15]（或b[15]）
        overflow <= (a[15] == b[15]) && (a[15] != sum[15]);
    end
end

endmodule