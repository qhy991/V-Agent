module alu (
    input [31:0] a,
    input [31:0] b,
    input [3:0] op,
    output reg [31:0] result
);

    always_comb begin
        case (op)
            4'b0000: result = a + b; // Add
            4'b0001: result = a - b; // Subtract
            4'b0010: result = a & b; // AND
            4'b0011: result = a | b; // OR
            4'b0100: result = a ^ b; // XOR
            default: result = 32'h0;
        endcase
    end

endmodule