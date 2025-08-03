module adder_16bit #(
    parameter WIDTH = 16
) (
    input               clk,
    input               rst,
    input  [WIDTH-1:0]  a,
    input  [WIDTH-1:0]  b,
    input               cin,
    output reg [WIDTH-1:0] sum,
    output reg          cout,
    output reg          overflow
);

// Internal signals for ripple carry
wire [WIDTH-1:0] carry;

// Generate carry chain using full adders
genvar i;
generate
    // First stage (LSB)
    assign carry[0] = cin;

    // Full adder chain
    for (i = 0; i < WIDTH-1; i = i + 1) begin : fa_chain
        assign carry[i+1] = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
    end

    // Final carry out
    assign cout = carry[WIDTH-1];

    // Sum generation
    always @(*) begin
        sum = a ^ b ^ carry;
    end
endgenerate

// Overflow detection: signed overflow occurs when sign bits of inputs are same but differ from result
// For signed addition: overflow = (a[15] == b[15]) && (a[15] != sum[15])
always @(*) begin
    overflow = (a[15] == b[15]) && (a[15] != sum[15]);
end

// Synchronous reset and register update
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        sum <= sum;
        cout <= cout;
        overflow <= overflow;
    end
end

endmodule