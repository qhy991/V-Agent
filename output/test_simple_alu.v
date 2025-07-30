module simple_alu (
    input [3:0] a,
    input [3:0] b,
    input [1:0] op,
    output reg [3:0] result,
    output reg zero_flag
);

always @(*) begin
    case (op)
        2'b00: result = a + b;  // 加法
        2'b01: result = a - b;  // 减法
        2'b10: result = a & b;  // 与运算
        2'b11: result = a | b;  // 或运算
        default: result = 4'b0000;
    endcase
    
    zero_flag = (result == 4'b0000);
end

endmodule