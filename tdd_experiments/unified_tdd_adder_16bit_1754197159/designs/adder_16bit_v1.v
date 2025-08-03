module adder_16bit #(
    parameter WIDTH = 16
) (
    input           clk,
    input           rst,
    input  [WIDTH-1:0] a,
    input  [WIDTH-1:0] b,
    input           cin,
    output reg [WIDTH-1:0] sum,
    output reg      cout,
    output reg      overflow
);

// Internal signals for ripple carry chain
reg [WIDTH-1:0] internal_sum;
reg [WIDTH-1:0] carry;

// Register the outputs to avoid combinational loop and ensure proper timing
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Compute sum and carry using ripple carry structure
        // Bit 0
        {carry[0], internal_sum[0]} = a[0] + b[0] + cin;
        
        // Bits 1 to 15
        genvar i;
        generate
            for (i = 1; i < WIDTH; i = i + 1) begin : ripple_carry
                {carry[i], internal_sum[i]} = a[i] + b[i] + carry[i-1];
            end
        endgenerate
        
        // Assign final outputs
        sum <= internal_sum;
        cout <= carry[WIDTH-1];
        
        // Overflow detection for signed addition:
        // Overflow occurs when two positive numbers produce a negative result,
        // or two negative numbers produce a positive result.
        // This is detected by XOR of the last two carry bits (carry[14] and carry[15])
        // But since we're using full adders, overflow = carry[15] XOR carry[14]
        overflow <= carry[WIDTH-1] ^ carry[WIDTH-2];
    end
end

endmodule