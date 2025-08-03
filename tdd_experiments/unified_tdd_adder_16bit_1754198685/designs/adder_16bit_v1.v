module adder_16bit #(
    parameter WIDTH = 16
) (
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input cin,
    output reg [WIDTH-1:0] sum,
    output reg cout,
    output reg overflow
);

// Internal signals for intermediate calculations
reg [WIDTH:0] internal_sum;
reg [WIDTH:0] temp_sum;

// Synchronous process for register updates
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Perform 16-bit addition with carry-in
        temp_sum = {1'b0, a} + {1'b0, b} + cin;
        internal_sum = temp_sum;

        // Output sum is the lower 16 bits of the result
        sum <= internal_sum[WIDTH-1:0];

        // Output carry is the MSB of the internal sum
        cout <= internal_sum[WIDTH];

        // Overflow detection for signed arithmetic:
        // Overflow occurs when two operands of same sign produce a result of opposite sign
        // i.e., (a_sign == b_sign) && (a_sign != result_sign)
        overflow <= (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != internal_sum[WIDTH-1]);
    end
end

endmodule