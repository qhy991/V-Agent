`timescale 1ns / 1ps

module tb_adder_16bit;

    // Signal declarations
    reg [15:0] a, b;
    reg cin;
    wire [15:0] sum;
    wire cout;
    wire overflow;

    // Clock and reset
    reg clk = 0;
    reg rst = 1;

    // Instantiate the DUT
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // Clock generation (10ns period)
    always #5 clk = ~clk;

    // Initial block for testbench
    initial begin
        // Waveform dump
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Initialize inputs
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;

        // Apply reset
        #20 rst = 0;

        // Test case 1: Add two positive numbers (0x7FFF + 0x0001) → no overflow
        #20 a = 16'h7FFF; b = 16'h0001; cin = 1'b0;
        #20 $display("Test case 1: 0x%h + 0x%h + %b -> sum=0x%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        #20 assert(sum == 16'h8000 && cout == 1'b0 && overflow == 1'b0) else $error("Test case 1 failed");

        // Test case 2: Add two large positive numbers (0x7FFF + 0x7FFF) → overflow
        #20 a = 16'h7FFF; b = 16'h7FFF; cin = 1'b0;
        #20 $display("Test case 2: 0x%h + 0x%h + %b -> sum=0x%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        #20 assert(sum == 16'hFFFE && cout == 1'b1 && overflow == 1'b1) else $error("Test case 2 failed");

        // Test case 3: Add two negative numbers (0x8000 + 0x8000) → overflow
        #20 a = 16'h8000; b = 16'h8000; cin = 1'b0;
        #20 $display("Test case 3: 0x%h + 0x%h + %b -> sum=0x%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        #20 assert(sum == 16'h0000 && cout == 1'b1 && overflow == 1'b1) else $error("Test case 3 failed");

        // Test case 4: Add positive and negative (0x7FFF + 0x8000) → no overflow
        #20 a = 16'h7FFF; b = 16'h8000; cin = 1'b0;
        #20 $display("Test case 4: 0x%h + 0x%h + %b -> sum=0x%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        #20 assert(sum == 16'hFFFF && cout == 1'b0 && overflow == 1'b0) else $error("Test case 4 failed");

        // Test case 5: Max value + 1 with cin=1 → check cout and overflow
        #20 a = 16'h7FFF; b = 16'h0000; cin = 1'b1;
        #20 $display("Test case 5: 0x%h + 0x%h + %b -> sum=0x%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        #20 assert(sum == 16'h8000 && cout == 1'b1 && overflow == 1'b1) else $error("Test case 5 failed");

        // Test case 6: Min value + 0 → verify sum and overflow
        #20 a = 16'h8000; b = 16'h0000; cin = 1'b0;
        #20 $display("Test case 6: 0x%h + 0x%h + %b -> sum=0x%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        #20 assert(sum == 16'h8000 && cout == 1'b0 && overflow == 1'b0) else $error("Test case 6 failed");

        // Test case 7: All zero inputs → sum=0, cout=0, overflow=0
        #20 a = 16'd0; b = 16'd0; cin = 1'b0;
        #20 $display("Test case 7: 0x%h + 0x%h + %b -> sum=0x%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        #20 assert(sum == 16'd0 && cout == 1'b0 && overflow == 1'b0) else $error("Test case 7 failed");

        // Test case 8: Edge case: a=0xFFFF, b=0xFFFF, cin=1 → sum=0xFFFE, cout=1, overflow=1
        #20 a = 16'hFFFF; b = 16'hFFFF; cin = 1'b1;
        #20 $display("Test case 8: 0x%h + 0x%h + %b -> sum=0x%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        #20 assert(sum == 16'hFFFE && cout == 1'b1 && overflow == 1'b1) else $error("Test case 8 failed");

        // Final simulation end
        #200 $display("All tests completed.");
        #20 $finish;
    end

    // Monitor signals
    initial begin
        $monitor("%t | a=0x%h, b=0x%h, cin=%b | sum=0x%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule