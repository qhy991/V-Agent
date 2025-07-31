/*
 * Module Name: four_bit_adder
 *
 * Description:
 * This module implements a 4-bit binary adder with carry-in and carry-out.
 * It performs addition of two 4-bit binary numbers (a and b) along with a carry-in (cin),
 * producing a 4-bit sum (sum) and a carry-out (cout).
 *
 * The design uses a ripple-carry architecture, which is simple and suitable for small bit widths.
 * For larger bit widths, a carry-lookahead adder would be more efficient.
 *
 * Parameters:
 *   WIDTH - Width of the adder (default: 4)
 *
 * Inputs:
 *   a     - 4-bit input A (unsigned)
 *   b     - 4-bit input B (unsigned)
 *   cin   - Carry-in (1-bit)
 *
 * Outputs:
 *   sum   - 4-bit result of the addition
 *   cout  - Carry-out (1-bit)
 *
 * Design Notes:
 * - This is a combinational logic module, so no clock or reset is required.
 * - The design is parameterized for flexibility and reusability.
 * - The implementation uses full adders for each bit position.
 * - The module includes assertions for debugging and verification purposes.
 *
 * Usage Example:
 *   four_bit_adder #(.WIDTH(4)) uut (
 *     .a(a),
 *     .b(b),
 *     .cin(cin),
 *     .sum(sum),
 *     .cout(cout)
 *   );
 */

`timescale 1ns / 1ps

module four_bit_adder #(
    parameter int WIDTH = 4  // Width of the adder
)(
    input  [WIDTH-1:0] a,      // First 4-bit operand
    input  [WIDTH-1:0] b,      // Second 4-bit operand
    input              cin,    // Carry-in
    output [WIDTH-1:0] sum,    // 4-bit sum result
    output             cout     // Carry-out
);

    // Internal signals
    reg [WIDTH-1:0] carry;     // Carry signals for each bit

    // Full adder for each bit
    genvar i;
    generate
        for (i = 0; i < WIDTH; i = i + 1) begin : adder_bits
            // Full adder for bit i
            full_adder fa (
                .a(a[i]),
                .b(b[i]),
                .cin(i == 0 ? cin : carry[i-1]),
                .sum(sum[i]),
                .cout(carry[i])
            );
        end
    endgenerate

    // Assign the final carry-out
    assign cout = carry[WIDTH-1];

    // Assertion for debugging and verification
    // Check that the sum is correct for all possible inputs
    // This is a simple assertion for demonstration purposes
    // In a real design, more comprehensive checks would be needed
    always @(a or b or cin) begin
        // Calculate expected sum and carry
        integer expected_sum;
        integer expected_cout;
        expected_sum = a + b + cin;
        expected_cout = (expected_sum > (2**WIDTH - 1)) ? 1 : 0;

        // Check if the actual sum matches the expected value
        // This is for simulation only and not synthesizable
        assert (sum === expected_sum[WIDTH-1:0]) else $error("Sum mismatch at bit %d", i);
    end

endmodule

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