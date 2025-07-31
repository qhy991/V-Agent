`timescale 1ns / 1ps

module four_bit_adder_testbench;

    // Testbench signals
    reg [3:0] a;
    reg [3:0] b;
    reg cin;
    wire [3:0] sum;
    wire cout;

    // Instantiate the four_bit_adder module
    four_bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    // Test vector generation
    initial begin
        // Test case 1: 0 + 0 + 0 = 0
        a = 4'b0000;
        b = 4'b0000;
        cin = 1'b0;
        #10;

        // Test case 2: 5 + 3 + 0 = 8 (0100 + 0011 = 0111)
        a = 4'b0100;
        b = 4'b0011;
        cin = 1'b0;
        #10;

        // Test case 3: 15 + 1 + 1 = 17 (1111 + 0001 + 1 = 10000)
        a = 4'b1111;
        b = 4'b0001;
        cin = 1'b1;
        #10;

        // Test case 4: 10 + 6 + 1 = 17 (1010 + 0110 + 1 = 10001)
        a = 4'b1010;
        b = 4'b0110;
        cin = 1'b1;
        #10;

        // Test case 5: 0 + 0 + 1 = 1
        a = 4'b0000;
        b = 4'b0000;
        cin = 1'b1;
        #10;

        // End of test
        $finish;
    end

    // Monitor outputs
    always @(posedge clk) begin
        $display("Time %t: a = %b, b = %b, cin = %b, sum = %b, cout = %b", $time, a, b, cin, sum, cout);
    end

endmodule