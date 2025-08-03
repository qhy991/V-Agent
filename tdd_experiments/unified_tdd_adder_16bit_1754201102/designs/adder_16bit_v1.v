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
wire [WIDTH:0] internal_sum;
wire [WIDTH:0] temp_sum;

// Generate the full addition with carry propagation
assign temp_sum = {1'b0, a} + {1'b0, b} + cin;

// Assign outputs
assign internal_sum = temp_sum;

// Output assignments
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        sum <= internal_sum[WIDTH-1:0];
        cout <= internal_sum[WIDTH];
        // Overflow detection for signed numbers:
        // Overflow occurs when two positive numbers are added and result is negative,
        // or two negative numbers are added and result is positive.
        // This is detected by comparing the sign bits of inputs and output.
        overflow <= ((a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != internal_sum[WIDTH-1]));
    end
end

endmodule