module task (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output reg [31:0] result,
    output reg zero
);

// ALU功能实现
always @(a or b or op) begin
    case (op)
        4'b0000: result = a + b;  // 加法
        4'b0001: result = a - b;  // 减法
        default: result = 32'b0;   // 其他操作码输出0
    endcase

    // 设置零标志：当结果为0时置1
    if (result == 32'b0) begin
        zero <= 1'b1;
    end else begin
        zero <= 1'b0;
    end
end

endmodule