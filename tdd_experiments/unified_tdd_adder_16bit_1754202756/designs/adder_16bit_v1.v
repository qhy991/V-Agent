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
wire [WIDTH-1:0] carry;

// Generate carry chain using full adders
genvar i;
generate
    // First full adder (LSB)
    full_adder fa0 (
        .a(a[0]),
        .b(b[0]),
        .cin(cin),
        .sum(sum[0]),
        .cout(carry[0])
    );

    // Remaining full adders
    for (i = 1; i < WIDTH; i = i + 1) begin : fa_chain
        full_adder fa (
            .a(a[i]),
            .b(b[i]),
            .cin(carry[i-1]),
            .sum(sum[i]),
            .cout(carry[i])
        );
    end
endgenerate

// Output carry and overflow
assign cout = carry[WIDTH-1];

// Overflow detection for signed addition: when sign of result differs from expected
// Expected sign is determined by sign bits of operands and carry into MSB
always @(*) begin
    if (rst) begin
        overflow = 1'b0;
    end else begin
        overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
    end
end

// Full adder primitive
primitive full_adder (
    input a, b, cin,
    output sum, cout
);
    table
        // a b cin : sum cout
        0 0 0 : 0 0;
        0 0 1 : 1 0;
        0 1 0 : 1 0;
        0 1 1 : 0 1;
        1 0 0 : 1 0;
        1 0 1 : 0 1;
        1 1 0 : 0 1;
        1 1 1 : 1 1;
    endtable
endprimitive

endmodule