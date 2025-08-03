`timescale 1ns/1ps

module tb_adder_16bit;

    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // Clock generation
    reg clk = 0;
    always #5 clk = ~clk;

    // Testbench instance of the DUT
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

        // Initialize inputs
        a = 16'b0;
        b = 16'b0;
        cin = 1'b0;

        // Wait for stable initialization
        #20;

        // Test 1: All zero inputs
        a = 16'b0;
        b = 16'b0;
        cin = 1'b0;
        #20;
        $display("Test 1: a=0, b=0, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        assert(sum == 16'h0 && cout == 1'b0 && overflow == 1'b0) else $error("Test 1 failed");

        // Test 2: Max positive
        a = 16'h7FFF;
        b = 16'b0;
        cin = 1'b0;
        #20;
        $display("Test 2: a=7FFF, b=0, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        assert(sum == 16'h7FFF && cout == 1'b0 && overflow == 1'b0) else $error("Test 2 failed");

        // Test 3: Max negative
        a = 16'h8000;
        b = 16'b0;
        cin = 1'b0;
        #20;
        $display("Test 3: a=8000, b=0, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        assert(sum == 16'h8000 && cout == 1'b0 && overflow == 1'b0) else $error("Test 3 failed");

        // Test 4: Positive overflow
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #20;
        $display("Test 4: a=7FFF, b=0001, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        assert(sum == 16'h8000 && cout == 1'b0 && overflow == 1'b1) else $error("Test 4 failed");

        // Test 5: Negative overflow
        a = 16'h8000;
        b = 16'hFFFF;
        cin = 1'b0;
        #20;
        $display("Test 5: a=8000, b=FFFF, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        assert(sum == 16'h7FFF && cout == 1'b0 && overflow == 1'b1) else $error("Test 5 failed");

        // Test 6: Carry propagation
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #20;
        $display("Test 6: a=FFFF, b=0001, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1'b1 && overflow == 1'b0) else $error("Test 6 failed");

        // Final check
        #20;
        $display("All tests completed.");
        $finish;
    end

    // Monitor signals
    initial begin
        $monitor("%t | a=%h, b=%h, cin=%b | sum=%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule