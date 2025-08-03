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

// Synchronous process to handle reset and update outputs on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Perform 16-bit addition with carry-in
        temp_sum = {1'b0, a} + {1'b0, b} + cin;
        internal_sum = temp_sum; // Full sum including carry-out

        // Assign sum output (lower 16 bits)
        sum <= internal_sum[15:0];

        // Assign cout (carry out from MSB)
        cout <= internal_sum[WIDTH];

        // Compute overflow: signed overflow occurs when both operands have same sign
        // but result has opposite sign. This happens when the carry into MSB differs
        // from carry out of MSB.
        // For signed overflow: (a[15] == b[15]) && (a[15] != sum[15])
        overflow <= (a[15] == b[15]) && (a[15] != sum[15]);
    end
end

endmodule