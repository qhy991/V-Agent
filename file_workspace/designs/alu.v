module alu(
    input clk,
    input rst_n,
    input [31:0] a,
    input [31:0] b,
    input [3:0] opcode,
    output reg [31:0] result,
    output reg zero
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        result <= 0;
        zero <= 1'b1;
    end else begin
        case (opcode)
            4'd0: result <= a + b;     // ADD
            4'd1: result <= a - b;     // SUB
            4'd2: result <= a & b;     // AND
            4'd3: result <= a | b;     // OR
            4'd4: result <= a ^ b;     // XOR
            4'd5: result <= a << b[4:0]; // SHIFT LEFT
            4'd6: result <= a >> b[4:0]; // SHIFT RIGHT
            default: result <= 0;
        endcase
        zero <= (result == 0);
    end
end

endmodule