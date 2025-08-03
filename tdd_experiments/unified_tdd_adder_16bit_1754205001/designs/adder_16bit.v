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

// Internal signals for ripple carry logic
wire [WIDTH-1:0] internal_sum;
wire [WIDTH-1:0] carry_out;

// Generate the full adder chain using generate block
genvar i;
generate
    for (i = 0; i < WIDTH; i = i + 1) begin : fa_chain
        if (i == 0) begin
            // First stage: use input cin
            assign carry_out[i] = (a[i] & b[i]) | (a[i] & cin) | (b[i] & cin);
            assign internal_sum[i] = a[i] ^ b[i] ^ cin;
        end else begin
            // Subsequent stages: use previous carry
            assign carry_out[i] = (a[i] & b[i]) | (a[i] & carry_out[i-1]) | (b[i] & carry_out[i-1]);
            assign internal_sum[i] = a[i] ^ b[i] ^ carry_out[i-1];
        end
    end
endgenerate

// Assign outputs
assign sum = internal_sum;
assign cout = carry_out[WIDTH-1];

// Overflow detection for signed addition:
// Overflow occurs when two positive numbers produce a negative result, or two negative numbers produce a positive result.
// This is detected by XOR of the carry into the MSB and the carry out of the MSB.
// For signed numbers, overflow = (carry_in_MSB) XOR (carry_out_MSB)
assign overflow = carry_out[WIDTH-2] ^ carry_out[WIDTH-1];

// Register outputs on clock edge (as per requirement to be in clock domain)
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        sum <= internal_sum;
        cout <= carry_out[WIDTH-1];
        overflow <= carry_out[WIDTH-2] ^ carry_out[WIDTH-1];
    end
end

endmodule