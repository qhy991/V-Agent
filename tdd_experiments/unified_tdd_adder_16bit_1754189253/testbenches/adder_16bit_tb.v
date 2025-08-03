`timescale 1ns / 1ps

module tb_adder_16bit;

    parameter WIDTH = 16;
    parameter PERIOD = 10;

    logic [WIDTH-1:0] a, b;
    logic cin;
    logic [WIDTH-1:0] sum;
    logic cout, overflow;

    adder_16bit #(.WIDTH(WIDTH)) dut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // Clock generation
    logic clk;
    always #5 clk = ~clk;

    // Reset generation
    logic rst_n;
    initial begin
        rst_n = 0;
        #20 rst_n = 1;
    end

    // Waveform dump
    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // Monitor signals
    initial begin
        $monitor("%t | a=%d, b=%d, cin=%b | sum=%d, cout=%b, overflow=%b", 
                 $time, a, b, cin, sum, cout, overflow);
    end

    // Testbench stimulus
    initial begin
        // Initialize inputs
        a = 0; b = 0; cin = 0;

        // Wait for reset to release
        @(posedge clk);

        // Test case 1: Overflow with two large positive numbers (+32767 + +32767)
        #10 a = 16'h7FFF; b = 16'h7FFF; cin = 0;
        @(posedge clk);
        #10;
        if (sum !== 16'hFFFE || cout !== 1 || overflow !== 1) begin
            $error("Test case 1 failed: Expected sum=0xFFFE, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test case 1 passed: +32767 + +32767 -> 0xFFFE with overflow");
        end

        // Test case 2: Overflow with two negative numbers (-32768 + -32768)
        #10 a = 16'h8000; b = 16'h8000; cin = 0;
        @(posedge clk);
        #10;
        if (sum !== 16'h0000 || cout !== 1 || overflow !== 1) begin
            $error("Test case 2 failed: Expected sum=0x0000, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test case 2 passed: -32768 + -32768 -> 0x0000 with overflow");
        end

        // Test case 3: Normal addition with no overflow (0 + 0)
        #10 a = 0; b = 0; cin = 0;
        @(posedge clk);
        #10;
        if (sum !== 0 || cout !== 0 || overflow !== 0) begin
            $error("Test case 3 failed: Expected sum=0, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test case 3 passed: 0 + 0 -> 0");
        end

        // Test case 4: Maximum unsigned value with carry-in (0xFFFF + 0x0001 + 1)
        #10 a = 16'hFFFF; b = 16'h0001; cin = 1;
        @(posedge clk);
        #10;
        if (sum !== 16'h0001 || cout !== 1 || overflow !== 0) begin
            $error("Test case 4 failed: Expected sum=0x0001, cout=1, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test case 4 passed: 0xFFFF + 0x0001 + 1 -> 0x0001 with carry out");
        end

        // Test case 5: Mixed signs (positive + negative) to verify no overflow
        #10 a = 16'h7FFF; b = 16'h8000; cin = 0;
        @(posedge clk);
        #10;
        if (sum !== 16'hFFFF || cout !== 0 || overflow !== 0) begin
            $error("Test case 5 failed: Expected sum=0xFFFF, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test case 5 passed: +32767 + -32768 -> 0xFFFF");
        end

        // Test case 6: Edge case where sum is exactly at boundary (0x7FFF + 0x0001)
        #10 a = 16'h7FFF; b = 16'h0001; cin = 0;
        @(posedge clk);
        #10;
        if (sum !== 16'h8000 || cout !== 0 || overflow !== 0) begin
            $error("Test case 6 failed: Expected sum=0x8000, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test case 6 passed: 0x7FFF + 0x0001 -> 0x8000");
        end

        // Final simulation end
        #100;
        $display("All test cases completed.");
        $finish;
    end

endmodule