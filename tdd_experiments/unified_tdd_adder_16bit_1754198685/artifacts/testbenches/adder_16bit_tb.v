`timescale 1ns / 1ps

module tb_adder_16bit;

    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // Clock generation
    parameter CLK_PERIOD = 10ns;
    reg clk;
    always #CLK_PERIOD clk = ~clk;

    // Testbench logic
    integer test_case;
    integer error_count = 0;

    // Instantiate the DUT
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    initial begin
        // Initialize signals
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;
        clk = 1'b0;

        // Enable waveform dumping
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Monitor signals
        $monitor("Time=%0t | a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", 
                 $time, a, b, cin, sum, cout, overflow);

        // Test case 1: a = 0, b = 0, cin = 0
        test_case = 1;
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;
        #20;
        if (sum !== 16'd0 || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case %0d failed. Expected sum=0, cout=0, overflow=0, got sum=16'h%h, cout=%b, overflow=%b", 
                     test_case, sum, cout, overflow);
            error_count++;
        end else begin
            $display("PASS: Test case %0d passed.", test_case);
        end

        // Test case 2: a = 16'hFFFF, b = 16'h0001, cin = 0
        test_case = 2;
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #20;
        if (sum !== 16'd0 || cout !== 1'b1 || overflow !== 1'b0) begin
            $display("ERROR: Test case %0d failed. Expected sum=0, cout=1, overflow=0, got sum=16'h%h, cout=%b, overflow=%b", 
                     test_case, sum, cout, overflow);
            error_count++;
        end else begin
            $display("PASS: Test case %0d passed.", test_case);
        end

        // Test case 3: a = 16'h7FFF, b = 16'h7FFF, cin = 0
        test_case = 3;
        a = 16'h7FFF;
        b = 16'h7FFF;
        cin = 1'b0;
        #20;
        if (sum !== 16'hFFFE || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case %0d failed. Expected sum=16'hFFFE, cout=1, overflow=1, got sum=16'h%h, cout=%b, overflow=%b", 
                     test_case, sum, cout, overflow);
            error_count++;
        end else begin
            $display("PASS: Test case %0d passed.", test_case);
        end

        // Test case 4: a = 16'h8000, b = 16'h8000, cin = 0
        test_case = 4;
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #20;
        if (sum !== 16'd0 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case %0d failed. Expected sum=0, cout=1, overflow=1, got sum=16'h%h, cout=%b, overflow=%b", 
                     test_case, sum, cout, overflow);
            error_count++;
        end else begin
            $display("PASS: Test case %0d passed.", test_case);
        end

        // Test case 5: a = 16'h7FFF, b = 16'h8000, cin = 0
        test_case = 5;
        a = 16'h7FFF;
        b = 16'h8000;
        cin = 1'b0;
        #20;
        if (sum !== 16'hFFFF || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case %0d failed. Expected sum=16'hFFFF, cout=0, overflow=0, got sum=16'h%h, cout=%b, overflow=%b", 
                     test_case, sum, cout, overflow);
            error_count++;
        end else begin
            $display("PASS: Test case %0d passed.", test_case);
        end

        // Final check
        if (error_count == 0) begin
            $display("All test cases passed successfully.");
        end else begin
            $display("%0d test cases failed.", error_count);
        end

        // End simulation after 1000 clock cycles
        #10000;
        $finish;
    end

endmodule