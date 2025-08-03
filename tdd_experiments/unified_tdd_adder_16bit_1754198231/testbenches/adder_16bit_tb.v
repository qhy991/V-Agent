`timescale 1ns / 1ps

module tb_adder_16bit;

    // Signal declarations
    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire       cout;
    wire       overflow;

    // Clock and reset
    reg clk = 0;
    reg rst = 1;

    // DUT instantiation
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

    // Initial block for testbench setup
    initial begin
        // Waveform dump
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Initialize signals
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;

        // Apply reset
        #20 rst = 0;

        // Test case 1: a = 0, b = 0, cin = 0 → sum = 0, cout = 0, overflow = 0
        #20 a = 16'd0;
        b = 16'd0;
        cin = 1'b0;
        #20;
        $display("Test case 1: a=0, b=0, cin=0 | sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'd0 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test case 1 failed!");
        end

        // Test case 2: a = 16'hFFFF, b = 16'hFFFF, cin = 1 → sum = 0, cout = 1, overflow = 1
        #20 a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b1;
        #20;
        $display("Test case 2: a=FFFF, b=FFFF, cin=1 | sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'd0 || cout !== 1'b1 || overflow !== 1'b1) begin
            $error("Test case 2 failed!");
        end

        // Test case 3: a = 16'h7FFF, b = 16'h7FFF, cin = 0 → sum = 16'hFFFE, cout = 1, overflow = 1
        #20 a = 16'h7FFF;
        b = 16'h7FFF;
        cin = 1'b0;
        #20;
        $display("Test case 3: a=7FFF, b=7FFF, cin=0 | sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'hFFFE || cout !== 1'b1 || overflow !== 1'b1) begin
            $error("Test case 3 failed!");
        end

        // Test case 4: a = 16'h8000, b = 16'h8000, cin = 0 → sum = 0, cout = 1, overflow = 1
        #20 a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #20;
        $display("Test case 4: a=8000, b=8000, cin=0 | sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'd0 || cout !== 1'b1 || overflow !== 1'b1) begin
            $error("Test case 4 failed!");
        end

        // Test case 5: a = 16'h0000, b = 16'h0000, cin = 1 → sum = 1, cout = 0, overflow = 0
        #20 a = 16'd0;
        b = 16'd0;
        cin = 1'b1;
        #20;
        $display("Test case 5: a=0000, b=0000, cin=1 | sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'd1 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test case 5 failed!");
        end

        // Monitor signals continuously
        $monitor("Time=%0t | a=%h, b=%h, cin=%b | sum=%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);

        // End simulation after 1000 clock cycles
        #20000; // 1000 * 20ns = 20000ns
        $display("Simulation completed.");
        $finish;
    end

endmodule