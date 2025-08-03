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

// Internal signals for carry propagation
reg [WIDTH-1:0] carry;

// Sequential logic for register updates on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'b0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Compute sum and carry using full adder chain
        // First bit: a[0] + b[0] + cin
        carry[0] <= (a[0] & b[0]) | (a[0] & cin) | (b[0] & cin);
        sum[0] <= a[0] ^ b[0] ^ cin;

        // Remaining bits: propagate carry
        genvar i;
        generate
            for (i = 1; i < WIDTH; i = i + 1) begin : carry_chain
                carry[i] <= (a[i] & b[i]) | (a[i] & carry[i-1]) | (b[i] & carry[i-1]);
                sum[i] <= a[i] ^ b[i] ^ carry[i-1];
            end
        endgenerate

        // Output carry is the final carry out from MSB
        cout <= carry[WIDTH-1];

        // Overflow detection for signed arithmetic:
        // Overflow occurs when two operands with same sign produce result with opposite sign.
        // For 16-bit signed numbers, sign bit is bit 15.
        // If both a and b are positive (sign=0) but sum is negative (sum[15]=1), overflow.
        // If both a and b are negative (sign=1) but sum is positive (sum[15]=0), overflow.
        overflow <= ((a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]));
    end
end

endmodule