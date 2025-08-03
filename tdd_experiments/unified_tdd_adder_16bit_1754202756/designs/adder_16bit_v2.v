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

// Internal signals for ripple carry chain
reg [WIDTH-1:0] internal_sum;
reg [WIDTH-1:0] carry;

// Initialize carry to input carry
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
        carry <= 1'b0;
    end else begin
        // Ripple carry adder implementation
        carry[0] <= cin;
        for (int i = 0; i < WIDTH; i = i + 1) begin
            internal_sum[i] <= a[i] ^ b[i] ^ carry[i];
            carry[i+1] <= (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
        end

        // Assign outputs
        sum <= internal_sum;
        cout <= carry[WIDTH];
        
        // Overflow detection for signed addition:
        // Overflow occurs when two positive numbers produce a negative result,
        // or two negative numbers produce a positive result.
        // This is detected by comparing the sign bits of inputs and output.
        // If sign(a) == sign(b) but sign(sum) != sign(a), overflow occurred.
        overflow <= (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
    end
end

endmodule