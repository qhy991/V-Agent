module alu_32bit(
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output [31:0] result,
    output       zero
);

    wire [31:0] sum;
    wire [31:0] and_result;
    wire [31:0] or_result;
    wire [31:0] xor_result;
    wire [31:0] nand_result;
    wire [31:0] nor_result;
    wire [31:0] xnor_result;
    wire [31:0] slt_result;
    wire [31:0] sll_result;
    wire [31:0] srl_result;
    wire [31:0] sra_result;
    wire [31:0] mul_result;
    wire [31:0] div_result;
    wire [31:0] rem_result;
    wire [31:0] shift_result;
    
    // Addition
    assign sum = a + b;
    
    // Logical operations
    assign and_result = a & b;
    assign or_result = a | b;
    assign xor_result = a ^ b;
    assign nand_result = ~(a & b);
    assign nor_result = ~(a | b);
    assign xnor_result = ~(a ^ b);
    
    // Comparison
    assign slt_result = (a < b) ? 32'h1 : 32'h0;
    
    // Shift operations
    assign sll_result = a << b[4:0];
    assign srl_result = a >> b[4:0];
    assign sra_result = $signed(a) >>> b[4:0];
    
    // Multiplication and division
    assign mul_result = a * b;
    assign div_result = (b != 32'h0) ? a / b : 32'h0;
    assign rem_result = (b != 32'h0) ? a % b : 32'h0;
    
    // Shift with immediate value
    assign shift_result = a << b[4:0];
    
    // Operation selection
    always @(*) begin
        case (op)
            4'b0000: result = sum;
            4'b0001: result = and_result;
            4'b0010: result = or_result;
            4'b0011: result = xor_result;
            4'b0100: result = nand_result;
            4'b0101: result = nor_result;
            4'b0110: result = xnor_result;
            4'b0111: result = slt_result;
            4'b1000: result = sll_result;
            4'b1001: result = srl_result;
            4'b1010: result = sra_result;
            4'b1011: result = mul_result;
            4'b1100: result = div_result;
            4'b1101: result = rem_result;
            4'b1110: result = shift_result;
            default: result = 32'h0;
        endcase
    end
    
    assign zero = (result == 32'h0) ? 1'b1 : 1'b0;
    
endmodule