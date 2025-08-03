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
reg [WIDTH-1:0] carry;

// Sequential logic for register outputs (synchronous)
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= {WIDTH{1'b0}};
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Compute sum and carry using ripple-carry structure
        // Bit 0
        carry[0] <= cin;
        sum[0] <= a[0] ^ b[0] ^ carry[0];
        carry[1] <= (a[0] & b[0]) | (a[0] & carry[0]) | (b[0] & carry[0]);

        // Bits 1 to 14
        genvar i;
        generate
            for (i = 1; i < WIDTH - 1; i = i + 1) begin : ripple_carry
                carry[i] <= (a[i] & b[i]) | (a[i] & carry[i-1]) | (b[i] & carry[i-1]);
                sum[i] <= a[i] ^ b[i] ^ carry[i-1];
            end
        endgenerate

        // Bit 15 (MSB)
        carry[WIDTH-1] <= (a[WIDTH-1] & b[WIDTH-1]) | (a[WIDTH-1] & carry[WIDTH-2]) | (b[WIDTH-1] & carry[WIDTH-2]);
        sum[WIDTH-1] <= a[WIDTH-1] ^ b[WIDTH-1] ^ carry[WIDTH-2];

        // Output carry
        cout <= carry[WIDTH-1];

        // Overflow detection for signed addition:
        // Overflow occurs when two positive numbers produce negative result, or two negative numbers produce positive result.
        // This is detected by XOR of the carry into MSB and carry out of MSB.
        overflow <= carry[WIDTH-2] ^ carry[WIDTH-1];
    end
end

endmodule