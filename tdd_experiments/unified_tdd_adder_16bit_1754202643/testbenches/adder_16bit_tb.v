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

        // Initialize inputs
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;

        // Test case 1: Add two positive numbers with no overflow (0x7FFF + 0x0001)
        #100;
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #100;
        $display("Test case 1: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h8000 && cout == 1'b0 && overflow == 1'b0) else $error("Test case 1 failed");

        // Test case 2: Add two negative numbers that cause overflow (0x8000 + 0x8000)
        #100;
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #100;
        $display("Test case 2: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1'b1 && overflow == 1'b1) else $error("Test case 2 failed");

        // Test case 3: Add large positive and negative numbers (0xFFFF + 0x0001)
        #100;
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #100;
        $display("Test case 3: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1'b1 && overflow == 1'b0) else $error("Test case 3 failed");

        // Test case 4: Edge case with max value and cin=1 (0xFFFF + 0x0000 + 1)
        #100;
        a = 16'hFFFF;
        b = 16'h0000;
        cin = 1'b1;
        #100;
        $display("Test case 4: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1'b1 && overflow == 1'b0) else $error("Test case 4 failed");

        // Test case 5: Zero inputs with cin=1
        #100;
        a = 16'd0;
        b = 16'd0;
        cin = 1'b1;
        #100;
        $display("Test case 5: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0001 && cout == 1'b0 && overflow == 1'b0) else $error("Test case 5 failed");

        #1000;
        $finish;
    end

    initial begin
        $monitor("%t | a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule