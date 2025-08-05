module test_adder(
    input [1:0] a,
    input [1:0] b,
    output reg [2:0] sum,
    input clk,
    input rst
);

// 内部信号声明
reg [2:0] temp_sum;

// 功能实现
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 3'b000; // 复位时清零
    end else begin
        temp_sum <= a + b; // 计算加法结果
        sum <= temp_sum;   // 将结果赋给输出
    end
end

endmodule