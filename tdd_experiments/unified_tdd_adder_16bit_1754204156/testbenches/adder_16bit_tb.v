`timescale 1ns / 1ps

module tb_adder_16bit;

    reg [15:0] a, b;
    reg cin;
    wire [15:0] sum;
    wire cout;
    wire overflow;

    // Instance of the DUT
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // Clock generation
    reg clk = 0;
    always #5 clk = ~clk; // 10ns period

    // Testbench logic
    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Initialize inputs
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;

        // Wait for reset to complete
        #20;

        // Test case 1: Add two positive numbers within range (0x7FFF + 0x0001)
        $display("Test case 1: 0x7FFF + 0x0001 with cin=0");
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #10;
        $display("Time %0t: a=16'h%h, b=16'h%h, cin=%b, sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
        assert(sum == 16'h8000 && cout == 1'b0 && overflow == 1'b0) else $error("Test case 1 failed");

        // Test case 2: Add two negative numbers that cause overflow (0xFFFF + 0xFFFF)
        $display("Test case 2: 0xFFFF + 0xFFFF with cin=0");
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b0;
        #10;
        $display("Time %0t: a=16'h%h, b=16'h%h, cin=%b, sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
        assert(sum == 16'hFFFE && cout == 1'b1 && overflow == 1'b1) else $error("Test case 2 failed");

        // Test case 3: Add large positive and negative number without overflow
        $display("Test case 3: 0x7FFF + 0x8000 with cin=0");
        a = 16'h7FFF;
        b = 16'h8000;
        cin = 1'b0;
        #10;
        $display("Time %0t: a=16'h%h, b=16'h%h, cin=%b, sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
        assert(sum == 16'hFFFE && cout == 1'b0 && overflow == 1'b0) else $error("Test case 3 failed");

        // Test case 4: Edge case with max value (0xFFFF + 0x0000 + 1 carry-in)
        $display("Test case 4: 0xFFFF + 0x0000 with cin=1");
        a = 16'hFFFF;
        b = 16'h0000;
        cin = 1'b1;
        #10;
        $display("Time %0t: a=16'h%h, b=16'h%h, cin=%b, sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1'b1 && overflow == 1'b0) else $error("Test case 4 failed");

        // Test case 5: Zero inputs with carry-in to test cout behavior
        $display("Test case 5: 0x0000 + 0x0000 with cin=1");
        a = 16'd0;
        b = 16'd0;
        cin = 1'b1;
        #10;
        $display("Time %0t: a=16'h%h, b=16'h%h, cin=%b, sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
        assert(sum == 16'd1 && cout == 1'b0 && overflow == 1'b0) else $error("Test case 5 failed");

        // Final check
        #100;
        $display("All tests completed.");
        $finish;
    end

    // Monitor signals
    initial begin
        $monitor("%0t: a=16'h%h, b=16'h%h, cin=%b, sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule