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
reg carry_in, carry_out;
reg [WIDTH-1:0] not_b;

// Register for zero and overflow flags (synchronous)
always @(posedge clk or posedge rst) begin
    if (rst) begin
        zero <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Update zero flag: set if result is zero
        zero <= (alu_result == 0) ? 1'b1 : 1'b0;

        // Update overflow flag only for arithmetic operations
        case (op)
            4'b0000, 4'b0001: begin // ADD, SUB
                overflow <= (signed_a[WIDTH-1] == signed_b[WIDTH-1]) && (signed_a[WIDTH-1] != sum[WIDTH-1]);
            end
            default:
                overflow <= 1'b0;
        endcase
    end
end

// Combinational logic for ALU operation
always @(*) begin
    // Initialize outputs
    alu_result = 0;
    not_b = ~b;

    // Sign extend inputs for signed arithmetic
    signed_a = a;
    signed_b = b;

    // Determine operation
    case (op)
        4'b0000: begin // ADD
            alu_result = a + b;
        end
        4'b0001: begin // SUB
            alu_result = a - b;
        end
        4'b0010: begin // AND
            alu_result = a & b;
        end
        4'b0011: begin // OR
            alu_result = a | b;
        end
        4'b0100: begin // XOR
            alu_result = a ^ b;
        end
        4'b0101: begin // NOT
            alu_result = ~a;
        end
        4'b0110: begin // EQ
            alu_result = (a == b) ? 32'd1 : 32'd0;
        end
        4'b0111: begin // LT (signed)
            alu_result = (signed_a < signed_b) ? 32'd1 : 32'd0;
        end
        4'b1000: begin // GT (signed)
            alu_result = (signed_a > signed_b) ? 32'd1 : 32'd0;
        end
        default: begin
            alu_result = 32'd0;
        end
    endcase

    // Update the result register
    result = alu_result;
end

endmodule