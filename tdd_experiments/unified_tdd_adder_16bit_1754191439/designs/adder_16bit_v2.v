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

// Internal signals for carry propagation
reg [WIDTH-1:0] carry;

// Sequential logic: register outputs on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Compute sum and carry using ripple-carry adder
        carry[0] <= cin;
        for (int i = 0; i < WIDTH-1; i = i + 1) begin
            carry[i+1] <= (a[i] & b[i] & carry[i]) | (a[i] & ~b[i] & ~carry[i]) | (~a[i] & b[i] & ~carry[i]) | (~a[i] & ~b[i] & carry[i]);
        end

        // Output sum is the XOR of inputs and carry-in at each bit
        for (int i = 0; i < WIDTH; i = i + 1) begin
            sum[i] <= a[i] ^ b[i] ^ carry[i];
        end

        // Final carry out
        cout <= carry[WIDTH-1];

        // Overflow detection for signed addition:
        // Overflow occurs when two positive numbers produce a negative result,
        // or two negative numbers produce a positive result.
        // This is detected by comparing the sign bits of operands and result.
        overflow <= (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
    end
end

endmodule