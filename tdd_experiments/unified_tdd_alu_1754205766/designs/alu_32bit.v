module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output reg [31:0] result,
    output reg zero,
    output reg overflow
);

    // Internal signals
    wire [31:0] sum;
    wire carry_out;
    wire [31:0] not_b;

    // Compute NOT of b for subtraction
    assign not_b = ~b;

    // Full adder for addition and subtraction
    assign {carry_out, sum} = a + not_b + (op[0] ? 1'b1 : 1'b0);

    // Combinational logic for ALU operations
    always @(*) begin
        case (op)
            4'b0000: begin  // ADD
                result = a + b;
                overflow = (a[31] == b[31]) && (result[31] != a[31]);
            end
            4'b0001: begin  // SUB
                result = a - b;
                overflow = (a[31] != b[31]) && (result[31] != a[31]);
            end
            4'b0010: begin  // AND
                result = a & b;
                overflow = 1'b0;
            end
            4'b0011: begin  // OR
                result = a | b;
                overflow = 1'b0;
            end
            4'b0100: begin  // XOR
                result = a ^ b;
                overflow = 1'b0;
            end
            4'b0101: begin  // NOT
                result = ~a;
                overflow = 1'b0;
            end
            4'b0110: begin  // EQ
                result = (a == b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end
            4'b0111: begin  // LT (signed)
                result = (a < b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end
            4'b1000: begin  // GT (signed)
                result = (a > b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end
            default: begin
                result = 32'd0;
                overflow = 1'b0;
            end
        endcase

        // Zero flag: set if result is zero
        zero = (result == 32'd0) ? 1'b1 : 1'b0;
    end

endmodule