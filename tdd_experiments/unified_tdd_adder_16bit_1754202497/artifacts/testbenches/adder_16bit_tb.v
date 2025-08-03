`timescale 1ns / 1ps

module tb_adder_16bit;

    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

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
    parameter CLK_PERIOD = 10ns;
    reg clk;
    always #CLK_PERIOD clk = ~clk;

    // Initial block for testbench
    initial begin
        // Initialize inputs
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;

        // Enable waveform dumping
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Monitor signals
        $monitor("%t | a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);

        // Test case 1: a = 0x7FFF, b = 0x0001, cin = 0 → no overflow
        #20 a = 16'h7FFF; b = 16'h0001; cin = 1'b0;
        #20;
        if (sum !== 16'h8000 || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case 1 failed. Expected sum=0x8000, cout=0, overflow=0");
        end else begin
            $display("PASS: Test case 1 passed.");
        end

        // Test case 2: a = 0x7FFF, b = 0x0001, cin = 1 → overflow
        #20 a = 16'h7FFF; b = 16'h0001; cin = 1'b1;
        #20;
        if (sum !== 16'h8000 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 2 failed. Expected sum=0x8000, cout=1, overflow=1");
        end else begin
            $display("PASS: Test case 2 passed.");
        end

        // Test case 3: a = 0x8000, b = 0x8000, cin = 0 → overflow (negative + negative)
        #20 a = 16'h8000; b = 16'h8000; cin = 1'b0;
        #20;
        if (sum !== 16'h0000 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 3 failed. Expected sum=0x0000, cout=1, overflow=1");
        end else begin
            $display("PASS: Test case 3 passed.");
        end

        // Test case 4: a = 0xFFFF, b = 0xFFFF, cin = 1 → max value with carry
        #20 a = 16'hFFFF; b = 16'hFFFF; cin = 1'b1;
        #20;
        if (sum !== 16'hFFFE || cout !== 1'b1 || overflow !== 1'b0) begin
            $display("ERROR: Test case 4 failed. Expected sum=0xFFFE, cout=1, overflow=0");
        end else begin
            $display("PASS: Test case 4 passed.");
        end

        // Test case 5: a = 0x0000, b = 0x0000, cin = 0 → zero case
        #20 a = 16'd0; b = 16'd0; cin = 1'b0;
        #20;
        if (sum !== 16'd0 || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case 5 failed. Expected sum=0, cout=0, overflow=0");
        end else begin
            $display("PASS: Test case 5 passed.");
        end

        // Finish simulation after 1000 clock cycles
        #20000;
        $display("Simulation completed successfully.");
        $finish;
    end

    // Initial block to start clock
    initial begin
        clk = 0;
    end

endmodule