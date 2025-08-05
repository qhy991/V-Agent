module alu_8bit (
    input wire [7:0] a,
    input wire [7:0] b,
    input wire [1:0] op,
    output reg [7:0] result,
    output reg zero
);

    always @(*) begin
        case (op)
            2'b00: result = a + b;  // 加法
            2'b01: result = a - b;  // 减法
            2'b10: result = a & b;  // 与运算
            2'b11: result = a | b;  // 或运算
            default: result = 8'b0;
        endcase
        
        zero = (result == 8'b0);
    end

endmodule