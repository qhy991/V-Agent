`timescale 1ns / 1ps

module tb_adder_16bit;

    reg [15:0] a, b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // Instantiate DUT
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Test case 1: Positive + Positive → No overflow
        a = 16'h7FFF; b = 16'h0001; cin = 1'b0;
        #10;
        $display("Test 1: a=16'h%h, b=16'h%h, cin=%b => sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        // Test case 2: Negative + Negative → Overflow
        a = 16'h8000; b = 16'h8000; cin = 1'b0;
        #10;
        $display("Test 2: a=16'h%h, b=16'h%h, cin=%b => sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        // Test case 3: Large positive + small negative
        a = 16'hFFFF; b = 16'h0001; cin = 1'b0;
        #10;
        $display("Test 3: a=16'h%h, b=16'h%h, cin=%b => sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        // Test case 4: Max value + 0 + cin=1
        a = 16'hFFFF; b = 16'h0000; cin = 1'b1;
        #10;
        $display("Test 4: a=16'h%h, b=16'h%h, cin=%b => sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        // Test case 5: Zero + zero + cin=1
        a = 16'h0000; b = 16'h0000; cin = 1'b1;
        #10;
        $display("Test 5: a=16'h%h, b=16'h%h, cin=%b => sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        #10;
        $finish;
    end

endmodule