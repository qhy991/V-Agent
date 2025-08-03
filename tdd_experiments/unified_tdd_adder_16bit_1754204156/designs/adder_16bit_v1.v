module adder_16bit #(
    parameter WIDTH = 16
) (
    input           clk,
    input           rst,
    input  [WIDTH-1:0] a,
    input  [WIDTH-1:0] b,
    input             cin,
    output reg [WIDTH-1:0] sum,
    output reg        cout,
    output reg        overflow
);

// Internal signals for intermediate calculations
wire [WIDTH:0] full_sum;
wire [WIDTH:0] temp_sum;

// Generate the full addition result including carry-in
assign temp_sum = {1'b0, a} + {1'b0, b} + cin;

// Assign outputs
assign full_sum = temp_sum;

// Output sum is the lower WIDTH bits of the full sum
always @(*) begin
    sum = full_sum[WIDTH-1:0];
end

// Output carry is the final carry out from the addition
always @(*) begin
    cout = full_sum[WIDTH];
end

// Overflow detection for signed arithmetic:
// Overflow occurs when two positive numbers are added and result is negative,
// or two negative numbers are added and result is positive.
// This is detected by XORing the carry into the sign bit and the carry out of the sign bit.
always @(*) begin
    overflow = (a[WIDTH-1] ^ b[WIDTH-1]) & (a[WIDTH-1] ^ full_sum[WIDTH-1]);
end

endmodule