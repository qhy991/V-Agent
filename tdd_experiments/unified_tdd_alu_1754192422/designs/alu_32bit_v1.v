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
reg [WIDTH-1:0] temp_a, temp_b;
reg signed [WIDTH-1:0] signed_a, signed_b;
reg signed [WIDTH-1:0] sum;
reg signed [WIDTH-1:0] diff;

// Register for zero and overflow flags
reg zero_reg;
reg overflow_reg;

// Assign inputs to internal registers for consistent timing
always @(posedge clk or posedge rst) begin
    if (rst) begin
        result <= 32'b0;
        zero <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Update result, zero, and overflow based on op
        case (op)
            4'b0000: begin // ADD
                signed_a = a;
                signed_b = b;
                sum = signed_a + signed_b;
                alu_result = sum;
                zero_reg = (sum == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = (signed_a[WIDTH-1] == signed_b[WIDTH-1]) && 
                               (signed_a[WIDTH-1] != sum[WIDTH-1]);
            end

            4'b0001: begin // SUB
                signed_a = a;
                signed_b = b;
                diff = signed_a - signed_b;
                alu_result = diff;
                zero_reg = (diff == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = (signed_a[WIDTH-1] != signed_b[WIDTH-1]) && 
                               (signed_a[WIDTH-1] != diff[WIDTH-1]);
            end

            4'b0010: begin // AND
                alu_result = a & b;
                zero_reg = (alu_result == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = 1'b0; // No overflow in logic ops
            end

            4'b0011: begin // OR
                alu_result = a | b;
                zero_reg = (alu_result == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = 1'b0;
            end

            4'b0100: begin // XOR
                alu_result = a ^ b;
                zero_reg = (alu_result == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = 1'b0;
            end

            4'b0101: begin // NOT
                alu_result = ~a;
                zero_reg = (alu_result == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = 1'b0;
            end

            4'b0110: begin // EQ
                alu_result = (a == b) ? 32'd1 : 32'd0;
                zero_reg = (alu_result == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = 1'b0;
            end

            4'b0111: begin // LT (signed)
                alu_result = (signed'(a) < signed'(b)) ? 32'd1 : 32'd0;
                zero_reg = (alu_result == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = 1'b0;
            end

            4'b1000: begin // GT (signed)
                alu_result = (signed'(a) > signed'(b)) ? 32'd1 : 32'd0;
                zero_reg = (alu_result == 32'd0) ? 1'b1 : 1'b0;
                overflow_reg = 1'b0;
            end

            default: begin
                alu_result = 32'd0;
                zero_reg = 1'b1;
                overflow_reg = 1'b0;
            end
        endcase

        // Update outputs
        result <= alu_result;
        zero <= zero_reg;
        overflow <= overflow_reg;
    end
end

endmodule