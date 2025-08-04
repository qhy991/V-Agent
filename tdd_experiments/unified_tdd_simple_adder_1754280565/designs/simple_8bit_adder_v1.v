module simple_8bit_adder (
    input clk,
    input rst,
    input [7:0] a,
    input [7:0] b,
    input cin,
    output reg [7:0] sum,
    output reg cout
);

    // 内部信号声明
    reg [8:0] temp_sum;

    // 时序逻辑实现
    always @(posedge clk) begin
        if (rst) begin
            sum <= 8'b0;
            cout <= 1'b0;
        end else begin
            // 计算8位加法和进位
            temp_sum <= {1'b0, a} + {1'b0, b} + cin;
            sum <= temp_sum[7:0];
            cout <= temp_sum[8];
        end
    end

endmodule