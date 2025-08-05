module four_bit_adder(
    input      [3:0] a,    // 4-bit input A
    input      [3:0] b,    // 4-bit input B
    input            cin,  // Carry-in
    output reg [3:0] sum,  // 4-bit sum output
    output reg       cout  // Carry-out
);

    // Internal carry signals
    wire [3:0] carry;

    // Full adder module definition
    module full_adder(
        input  a, b, cin,
        output sum, cout
    );
        assign sum = a ^ b ^ cin;
        assign cout = (a & b) | (cin & (a ^ b));
    endmodule