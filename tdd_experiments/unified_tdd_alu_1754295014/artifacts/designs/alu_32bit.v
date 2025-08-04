module alu_32bit(
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output [31:0] result,
    output       carry_out
);

    wire [31:0] sum;
    wire carry;
    
    // ALU operations
    assign sum = a + b;
    assign carry = (a + b) > 32'hFFFFFFFF;
    
    always @(*) begin
        case (op)
            4'b0000: result = a + b;     // ADD
            4'b0001: result = a - b;     // SUB
            4'b0010: result = a & b;     // AND
            4'b0011: result = a | b;     // OR
            4'b0100: result = a ^ b;     // XOR
            4'b0101: result = ~a;        // NOT
            4'b0110: result = a << b[4:0]; // SHIFT LEFT
            4'b0111: result = a >> b[4:0]; // SHIFT RIGHT
            4'b1000: result = a * b;     // MUL
            4'b1001: result = a / b;     // DIV
            default: result = 32'h0;
        endcase
    end
    
    assign carry_out = carry;
    
endmodule