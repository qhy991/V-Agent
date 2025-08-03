module adder_16bit #(
    parameter WIDTH = 16
) (
    input               clk,
    input               rst,
    input  [WIDTH-1:0]  a,
    input  [WIDTH-1:0]  b,
    input               cin,
    output logic [WIDTH-1:0] sum,
    output logic        cout,
    output logic        overflow
);

// Internal signals for ripple-carry chain
logic [WIDTH-1:0] carry;

// Generate the ripple-carry adder using full adders
generate
    genvar i;
    for (i = 0; i < WIDTH; i++) begin : fa_chain
        // Full adder for each bit
        if (i == 0) begin
            assign carry[i] = cin;
        end else begin
            assign carry[i] = (a[i-1] & b[i-1]) | (a[i-1] & carry[i-1]) | (b[i-1] & carry[i-1]);
        end

        assign sum[i] = a[i] ^ b[i] ^ carry[i];
    end
endgenerate

// Output carry is the final carry out from the most significant bit
assign cout = carry[WIDTH-1];

// Overflow detection for signed addition:
// Overflow occurs when both operands have the same sign and result has opposite sign.
// This happens when: (a[15] == b[15]) && (a[15] != sum[15])
assign overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);

endmodule