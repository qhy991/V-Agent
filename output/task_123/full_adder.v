/*
 * Module Name: full_adder
 *
 * Description:
 * This module implements a full adder that adds three 1-bit inputs (a, b, cin)
 * and produces a 1-bit sum and a 1-bit carry-out.
 *
 * Inputs:
 *   a     - 1-bit input A
 *   b     - 1-bit input B
 *   cin   - Carry-in (1-bit)
 *
 * Outputs:
 *   sum   - 1-bit sum result
 *   cout  - Carry-out (1-bit)
 *
 * Design Notes:
 * - This is a basic full adder implementation using XOR and AND/OR gates.
 * - The design is parameterized for potential future extensions.
 */
module full_adder (
    input  a,
    input  b,
    input  cin,
    output sum,
    output cout
);

    // Intermediate signals
    wire xor1;
    wire and1;
    wire and2;
    wire or1;

    // XOR for sum calculation
    assign xor1 = a ^ b;
    assign sum = xor1 ^ cin;

    // AND gates for carry calculation
    assign and1 = a & b;
    assign and2 = xor1 & cin;

    // OR gate for carry-out
    assign or1 = and1 | and2;
    assign cout = or1;

endmodule