`timescale 1ns / 1ps

module test_four_bit_adder;

    // Inputs
    reg [3:0] a;
    reg [3:0] b;
    reg cin;

    // Outputs
    wire [3:0] sum;
    wire cout;

    // Instantiate the Unit Under Test (UUT)
    four_bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    // Test cases
    initial begin
        // Test case 1: 0 + 0 + 0 = 0
        a = 4'b0000;
        b = 4'b0000;
        cin = 1'b0;
        #10;

        // Test case 2: 1 + 1 + 0 = 2
        a = 4'b0001;
        b = 4'b0001;
        cin = 1'b0;
        #10;

        // Test case 3: 3 + 5 + 0 = 8
        a = 4'b0011;
        b = 4'b0101;
        cin = 1'b0;
        #10;

        // Test case 4: 15 + 1 + 1 = 17 (with carry)
        a = 4'b1111;
        b = 4'b0001;
        cin = 1'b1;
        #10;

        // Test case 5: 10 + 5 + 0 = 15
        a = 4'b1010;
        b = 4'b0101;
        cin = 1'b0;
        #10;

        // Test case 6: 15 + 15 + 1 = 31 (with carry)
        a = 4'b1111;
        b = 4'b1111;
        cin = 1'b1;
        #10;

        $stop;
    end

endmodule