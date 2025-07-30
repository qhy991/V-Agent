module alu_32bit(
    input [31:0] a,
    input [31:0] b, 
    input [3:0] op,
    output reg [31:0] result,
    output zero,
    output overflow
);

assign zero = (result == 32'b0);
assign overflow = 1'b0; // 简化实现

always @(*) begin
    case(op)
        4'b0000: result = a + b;    // ADD
        4'b0001: result = a - b;    // SUB
        4'b0010: result = a & b;    // AND
        4'b0011: result = a | b;    // OR
        4'b0100: result = a ^ b;    // XOR
        4'b0101: result = ~a;       // NOT
        default: result = 32'b0;
    endcase
end

endmodule