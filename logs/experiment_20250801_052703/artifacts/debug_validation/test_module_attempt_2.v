module task (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output reg [31:0] result,
    output reg zero
);

always @(*) begin
    case (op)
        4'b0000: result = a + b;  // 加法
        4'b0001: result = a - b;  // 减法
        default: result = 32'b0;   // 其他操作码输出0
    endcase

    // 计算零标志
    zero = (result == 32'b0) ? 1'b1 : 1'b0;
end

endmodule