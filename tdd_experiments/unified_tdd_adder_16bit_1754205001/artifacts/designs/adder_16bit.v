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
wire [WIDTH-1:0] carry_out;
wire [WIDTH-1:0] internal_sum;

// Generate the full adder chain using generate block
generate
    genvar i;
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

// Overflow detection: signed overflow occurs when both operands have same sign but result has opposite sign
// For signed numbers, sign bit is MSB (bit 15)
always @(*) begin
    if ((a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != internal_sum[WIDTH-1])) begin
        overflow = 1'b1;
    end else begin
        overflow = 1'b0;
    end
end

endmodule