`timescale 1ns / 1ps

module tb_adder_16bit;

    parameter WIDTH = 16;
    parameter CLK_PERIOD = 10ns;

    // Signal declarations
    reg [WIDTH-1:0] a, b;
    reg cin;
    wire [WIDTH-1:0] sum;
    wire cout;
    wire overflow;

    // Clock and reset generation
    reg clk;
    initial begin
        clk = 0;
        forever #CLK_PERIOD/2 clk = ~clk;
    end

    // Testbench instance of the DUT
    adder_16bit #(.WIDTH(WIDTH)) uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // Monitor signals
    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // Test sequence
    initial begin
        // Initialize inputs
        a = 0;
        b = 0;
        cin = 0;

        // Basic addition: a = 1, b = 1, cin = 0 → sum = 2, cout = 0, overflow = 0
        #10 a = 16'h0001; b = 16'h0001; cin = 0;
        #10 $display("Test 1: a=1, b=1, cin=0 | sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'h0002 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 1 failed!");
        end

        // Carry propagation: a = 16'hFFFF, b = 1, cin = 0 → sum = 0, cout = 1, overflow = 0
        #10 a = 16'hFFFF; b = 16'h0001; cin = 0;
        #10 $display("Test 2: a=FFFF, b=1, cin=0 | sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'h0000 || cout !== 1'b1 || overflow !== 1'b0) begin
            $error("Test 2 failed!");
        end

        // Positive overflow: a = 16'h7FFF, b = 1, cin = 0 → sum = 16'h8000, cout = 1, overflow = 1
        #10 a = 16'h7FFF; b = 16'h0001; cin = 0;
        #10 $display("Test 3: a=7FFF, b=1, cin=0 | sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'h8000 || cout !== 1'b1 || overflow !== 1'b1) begin
            $error("Test 3 failed!");
        end

        // Negative overflow: a = 16'h8000, b = 16'h8000, cin = 0 → sum = 16'h0000, cout = 1, overflow = 1
        #10 a = 16'h8000; b = 16'h8000; cin = 0;
        #10 $display("Test 4: a=8000, b=8000, cin=0 | sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'h0000 || cout !== 1'b1 || overflow !== 1'b1) begin
            $error("Test 4 failed!");
        end

        // Normal case: a = 16'h7FFF, b = 16'h8000, cin = 0 → sum = -1, cout = 0, overflow = 0
        #10 a = 16'h7FFF; b = 16'h8000; cin = 0;
        #10 $display("Test 5: a=7FFF, b=8000, cin=0 | sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'hFFFF || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 5 failed!");
        end

        // Boundary values: a = 0, b = 0, cin = 0 → sum = 0, cout = 0, overflow = 0
        #10 a = 0; b = 0; cin = 0;
        #10 $display("Test 6: a=0, b=0, cin=0 | sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'h0000 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 6 failed!");
        end

        // All-zero inputs with carry-in: a = 0, b = 0, cin = 1 → sum = 1, cout = 0, overflow = 0
        #10 a = 0; b = 0; cin = 1;
        #10 $display("Test 7: a=0, b=0, cin=1 | sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        if (sum !== 16'h0001 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 7 failed!");
        end

        // Final simulation end
        #100 $display("All tests completed.");
        #100 $finish;
    end

endmodule