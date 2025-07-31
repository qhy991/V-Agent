/*
 * Module Name: four_bit_adder
 *
 * Description:
 * A 4-bit binary adder that adds two 4-bit numbers (a and b) along with a carry-in (cin)
 * and produces a 4-bit sum (sum) and a carry-out (cout).
 *
 * This implementation uses a ripple-carry architecture, which is simple and suitable for
 * small bit widths. For larger bit widths, a carry-lookahead adder would be more efficient.
 *
 * Parameters:
 *   WIDTH - The width of the adder (default: 4)
 *
 * Inputs:
 *   a      - 4-bit input number A
 *   b      - 4-bit input number B
 *   cin    - Carry-in signal
 *
 * Outputs:
 *   sum    - 4-bit result of the addition
 *   cout   - Carry-out signal
 *
 * Design Notes:
 * - This is a combinational logic module, so no clock or reset is required
 * - The design is parameterized for flexibility and reusability
 * - All signals are properly documented and named according to standard conventions
 * - The module is designed for easy verification and debugging
 */

`timescale 1ns / 1ps

module four_bit_adder #(
    parameter int WIDTH = 4
) (
    // 4-bit input number A
    input  [WIDTH-1:0] a,
    
    // 4-bit input number B
    input  [WIDTH-1:0] b,
    
    // Carry-in signal
    input              cin,
    
    // 4-bit sum output
    output [WIDTH-1:0] sum,
    
    // Carry-out signal
    output             cout
);

// Internal signals for intermediate carry values
wire [WIDTH:0] carry;

// Generate the full adders for each bit
genvar i;
generate
    for (i = 0; i < WIDTH; i = i + 1) begin : gen_full_adder
        // Full adder for bit i
        full_adder fa (
            .a(a[i]),
            .b(b[i]),
            .cin(carry[i]),
            .sum(sum[i]),
            .cout(carry[i+1])
        );
    end
endgenerate

// Assign the final carry-out
assign cout = carry[WIDTH];

// Assertion to check for valid input ranges (optional for synthesis)
// These assertions are typically used in simulation for verification
`ifdef SIMULATION
    // Check that inputs are within their valid ranges
    initial begin
        assert ($isunknown(a) || (a >= 0 && a < (1 << WIDTH))) else $error("Input a out of range");
        assert ($isunknown(b) || (b >= 0 && b < (1 << WIDTH))) else $error("Input b out of range");
        assert ($isunknown(cin) || (cin == 0 || cin == 1)) else $error("Carry-in out of range");
    end
`endif

endmodule

/*
 * Module Name: full_adder
 *
 * Description:
 * A single-bit full adder that adds two bits (a and b) along with a carry-in (cin)
 * and produces a sum bit (sum) and a carry-out (cout).
 *
 * Inputs:
 *   a      - Input bit A
 *   b      - Input bit B
 *   cin    - Carry-in signal
 *
 * Outputs:
 *   sum    - Sum bit
 *   cout   - Carry-out signal
 */

module full_adder (
    input  a,
    input  b,
    input  cin,
    output sum,
    output cout
);

// Calculate the sum using XOR
assign sum = a ^ b ^ cin;

// Calculate the carry-out using AND and OR gates
assign cout = (a & b) | (a & cin) | (b & cin);

endmodule