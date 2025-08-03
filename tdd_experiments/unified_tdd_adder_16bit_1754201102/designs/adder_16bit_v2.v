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

// Internal signals for carry propagation
logic [WIDTH-1:0] carry;

// Generate carry chain using ripple-carry structure
assign carry[0] = cin;
generate
    genvar i;
    for (i = 0; i < WIDTH-1; i = i + 1) begin : carry_chain
        assign carry[i+1] = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
    end
endgenerate

// Compute sum bits
assign sum = a ^ b ^ carry;

// Output carry
assign cout = carry[WIDTH-1];

// Overflow detection for signed arithmetic:
// Overflow occurs when two positive numbers produce a negative result,
// or two negative numbers produce a positive result.
// This is detected by comparing the sign of inputs and output.
assign overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);

endmodule