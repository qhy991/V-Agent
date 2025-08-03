`timescale 1ns / 1ps

module tb_adder_16bit;

    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    reg clk;
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Test case 1: Add two positive numbers with no overflow (0x7FFF + 0x0001)
        a = 16'h7FFF; b = 16'h0001; cin = 0;
        #100;
        $display("Test Case 1: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h8000 && cout == 0 && overflow == 0) else $error("Test Case 1 Failed");

        // Test case 2: Add two negative numbers with overflow (0x8000 + 0x8000)
        a = 16'h8000; b = 16'h8000; cin = 0;
        #100;
        $display("Test Case 2: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1 && overflow == 1) else $error("Test Case 2 Failed");

        // Test case 3: Add large positive and negative numbers (0xFFFF + 0x0001)
        a = 16'hFFFF; b = 16'h0001; cin = 0;
        #100;
        $display("Test Case 3: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1 && overflow == 0) else $error("Test Case 3 Failed");

        // Test case 4: Edge case with max value (0xFFFF + 0x0000 + cin=1)
        a = 16'hFFFF; b = 16'h0000; cin = 1;
        #100;
        $display("Test Case 4: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1 && overflow == 0) else $error("Test Case 4 Failed");

        // Test case 5: All zero inputs with cin=1 → sum=1, cout=0, overflow=0
        a = 16'h0000; b = 16'h0000; cin = 1;
        #100;
        $display("Test Case 5: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0001 && cout == 0 && overflow == 0) else $error("Test Case 5 Failed");

        #100;
        $display("All tests passed.");
        $finish;
    end

    initial begin
        $monitor("%t | a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule