module alu_32bit #(
    parameter WIDTH = 32
) (
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input [3:0] op,
    output reg [WIDTH-1:0] result,
    output reg zero,
    output reg overflow
);

// Internal signals
reg [WIDTH-1:0] alu_result;
reg [WIDTH-1:0] temp_b;
reg [WIDTH-1:0] carry_in;
reg [WIDTH-1:0] sum;
reg [WIDTH-1:0] diff;
reg [WIDTH-1:0] and_result;
reg [WIDTH-1:0] or_result;
reg [WIDTH-1:0] xor_result;
reg [WIDTH-1:0] not_result;
reg [WIDTH-1:0] eq_result;
reg [WIDTH-1:0] lt_result;
reg [WIDTH-1:0] gt_result;

// Register for zero and overflow flags
reg zero_reg;
reg overflow_reg;

// Combinational logic for NOT operation
always @(*) begin
    case (op)
        4'b0101: temp_b = ~b;
        default: temp_b = b;
    endcase
end

// Combinational logic for ALU operations
always @(*) begin
    alu_result = 32'd0;
    zero_reg = 1'b0;
    overflow_reg = 1'b0;

    case (op)
        // ADD
        4'b0000: begin
            {carry_in, sum} = a + temp_b;
            alu_result = sum;
            zero_reg = (sum == 32'd0);
            // Overflow detection for signed addition
            overflow_reg = (a[WIDTH-1] == temp_b[WIDTH-1]) && (sum[WIDTH-1] != a[WIDTH-1]);
        end

        // SUB
        4'b0001: begin
            {carry_in, diff} = a - temp_b;
            alu_result = diff;
            zero_reg = (diff == 32'd0);
            // Overflow detection for signed subtraction
            overflow_reg = (a[WIDTH-1] != temp_b[WIDTH-1]) && (diff[WIDTH-1] != a[WIDTH-1]);
        end

        // AND
        4'b0010: begin
            alu_result = a & temp_b;
            zero_reg = (alu_result == 32'd0);
        end

        // OR
        4'b0011: begin
            alu_result = a | temp_b;
            zero_reg = (alu_result == 32'd0);
        end

        // XOR
        4'b0100: begin
            alu_result = a ^ temp_b;
            zero_reg = (alu_result == 32'd0);
        end

        // NOT
        4'b0101: begin
            alu_result = ~a;
            zero_reg = (alu_result == 32'd0);
        end

        // EQ
        4'b0110: begin
            alu_result = (a == temp_b) ? 32'd1 : 32'd0;
            zero_reg = (alu_result == 32'd0);
        end

        // LT
        4'b0111: begin
            alu_result = (signed'(a) < signed'(temp_b)) ? 32'd1 : 32'd0;
            zero_reg = (alu_result == 32'd0);
        end

        // GT
        4'b1000: begin
            alu_result = (signed'(a) > signed'(temp_b)) ? 32'd1 : 32'd0;
            zero_reg = (alu_result == 32'd0);
        end

        default: alu_result = 32'd0;
    endcase
end

// Synchronous update of outputs
always @(posedge clk or posedge rst) begin
    if (rst) begin
        result <= 32'd0;
        zero <= 1'b0;
        overflow <= 1'b0;
    end else begin
        result <= alu_result;
        zero <= zero_reg;
        overflow <= overflow_reg;
    end
end

endmodule