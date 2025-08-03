`timescale 1ns / 1ps

module tb_adder_16bit;

    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // Clock generation
    reg clk = 0;
    always #5 clk = ~clk; // 10ns period

    // DUT instantiation
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // Waveform dump
    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // Testbench logic
    initial begin
        // Initialize inputs
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;

        // Wait for reset to stabilize
        #20;

        // Test 1: Add two positive numbers
        a = 16'h0001;
        b = 16'h0002;
        cin = 1'b0;
        #10;
        $display("Test 1: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        if (sum !== 16'h0003 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 1 failed: expected sum=3, got %h", sum);
        end

        // Test 2: Add two negative numbers (two's complement)
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b0;
        #10;
        $display("Test 2: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        if (sum !== 16'hFFFE || cout !== 1'b1 || overflow !== 1'b1) begin
            $error("Test 2 failed: expected sum=16'hFFFE, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end

        // Test 3: Large positive + small negative
        a = 16'h7FFF;
        b = 16'h8000;
        cin = 1'b0;
        #10;
        $display("Test 3: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        if (sum !== 16'hFFFF || cout !== 1'b0 || overflow !== 1'b1) begin
            $error("Test 3 failed: expected sum=16'hFFFF, cout=0, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end

        // Test 4: Max value + max value
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b0;
        #10;
        $display("Test 4: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        if (sum !== 16'hFFFE || cout !== 1'b1 || overflow !== 1'b1) begin
            $error("Test 4 failed: expected sum=16'hFFFE, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end

        // Test 5: Min value + min value
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #10;
        $display("Test 5: a=16'h%h, b=16'h%h, cin=%b -> sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        if (sum !== 16'h0000 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 5 failed: expected sum=0, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end

        // Finish simulation
        #100;
        $display("All tests completed.");
        $finish;
    end

    // Monitor signals
    initial begin
        $monitor("%t | a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule