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
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Compute sum and carry using ripple-carry structure
        // First bit
        {carry[0], sum[0]} = a[0] + b[0] + cin;
        
        // Remaining bits
        genvar i;
        generate
            for (i = 1; i < WIDTH; i = i + 1) begin : carry_chain
                {carry[i], sum[i]} = a[i] + b[i] + carry[i-1];
            end
        endgenerate

        // Output carry
        cout <= carry[WIDTH-1];

        // Overflow detection for signed addition:
        // Overflow occurs when two positive numbers produce negative result,
        // or two negative numbers produce positive result.
        // This is detected by XOR of the last two carry bits (carry[WIDTH-1] and carry[WIDTH-2])
        // But since we only have one carry out, we use the sign bits of operands and result
        // Specifically: overflow = (a[15] == b[15]) && (a[15] != sum[15])
        overflow <= (a[15] == b[15]) && (a[15] != sum[15]);
    end
end

endmodule