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

// Internal signals for ripple-carry adder
logic [WIDTH-1:0] carry;

// Carry generation and propagation logic
assign carry[0] = cin;
assign carry[1] = (a[0] & b[0]) | (a[0] & carry[0]) | (b[0] & carry[0]);
assign carry[2] = (a[1] & b[1]) | (a[1] & carry[1]) | (b[1] & carry[1]);
assign carry[3] = (a[2] & b[2]) | (a[2] & carry[2]) | (b[2] & carry[2]);
assign carry[4] = (a[3] & b[3]) | (a[3] & carry[3]) | (b[3] & carry[3]);
assign carry[5] = (a[4] & b[4]) | (a[4] & carry[4]) | (b[4] & carry[4]);
assign carry[6] = (a[5] & b[5]) | (a[5] & carry[5]) | (b[5] & carry[5]);
assign carry[7] = (a[6] & b[6]) | (a[6] & carry[6]) | (b[6] & carry[6]);
assign carry[8] = (a[7] & b[7]) | (a[7] & carry[7]) | (b[7] & carry[7]);
assign carry[9] = (a[8] & b[8]) | (a[8] & carry[8]) | (b[8] & carry[8]);
assign carry[10] = (a[9] & b[9]) | (a[9] & carry[9]) | (b[9] & carry[9]);
assign carry[11] = (a[10] & b[10]) | (a[10] & carry[10]) | (b[10] & carry[10]);
assign carry[12] = (a[11] & b[11]) | (a[11] & carry[11]) | (b[11] & carry[11]);
assign carry[13] = (a[12] & b[12]) | (a[12] & carry[12]) | (b[12] & carry[12]);
assign carry[14] = (a[13] & b[13]) | (a[13] & carry[13]) | (b[13] & carry[13]);
assign carry[15] = (a[14] & b[14]) | (a[14] & carry[14]) | (b[14] & carry[14]);

// Generate sum bits using XOR with carry
assign sum[0] = a[0] ^ b[0] ^ carry[0];
assign sum[1] = a[1] ^ b[1] ^ carry[1];
assign sum[2] = a[2] ^ b[2] ^ carry[2];
assign sum[3] = a[3] ^ b[3] ^ carry[3];
assign sum[4] = a[4] ^ b[4] ^ carry[4];
assign sum[5] = a[5] ^ b[5] ^ carry[5];
assign sum[6] = a[6] ^ b[6] ^ carry[6];
assign sum[7] = a[7] ^ b[7] ^ carry[7];
assign sum[8] = a[8] ^ b[8] ^ carry[8];
assign sum[9] = a[9] ^ b[9] ^ carry[9];
assign sum[10] = a[10] ^ b[10] ^ carry[10];
assign sum[11] = a[11] ^ b[11] ^ carry[11];
assign sum[12] = a[12] ^ b[12] ^ carry[12];
assign sum[13] = a[13] ^ b[13] ^ carry[13];
assign sum[14] = a[14] ^ b[14] ^ carry[14];
assign sum[15] = a[15] ^ b[15] ^ carry[15];

// Output carry is the final carry out from MSB
assign cout = carry[15];

// Overflow detection for signed addition:
// Overflow occurs when two positive numbers produce a negative result, or
// two negative numbers produce a positive result.
// This happens when the sign of the inputs are the same but different from the sign of the output.
assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);

endmodule