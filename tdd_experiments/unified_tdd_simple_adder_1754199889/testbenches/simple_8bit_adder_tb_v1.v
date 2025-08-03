`timescale 1ns / 1ps

module tb_simple_8bit_adder;

    reg [7:0] a;
    reg [7:0] b;
    reg cin;
    wire [7:0] sum;
    wire cout;

    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    reg clk;
    reg rst;

    initial begin
        $dumpfile("tb_simple_8bit_adder.vcd");
        $dumpvars(0, tb_simple_8bit_adder);

        clk = 0;
        rst = 1;
        #20 rst = 0;

        #100;
        // Test case 1: a=0, b=0, cin=0 → sum=0, cout=0
        a = 8'd0; b = 8'd0; cin = 1'b0;
        #10;
        if (sum !== 8'd0 || cout !== 1'b0) begin
            $display("FAIL: Test case 1 - Expected sum=0, cout=0, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test case 1 - sum=0, cout=0");
        end

        #100;
        // Test case 2: a=255, b=0, cin=0 → sum=255, cout=0
        a = 8'd255; b = 8'd0; cin = 1'b0;
        #10;
        if (sum !== 8'd255 || cout !== 1'b0) begin
            $display("FAIL: Test case 2 - Expected sum=255, cout=0, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test case 2 - sum=255, cout=0");
        end

        #100;
        // Test case 3: a=255, b=0, cin=1 → sum=0, cout=1
        a = 8'd255; b = 8'd0; cin = 1'b1;
        #10;
        if (sum !== 8'd0 || cout !== 1'b1) begin
            $display("FAIL: Test case 3 - Expected sum=0, cout=1, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test case 3 - sum=0, cout=1");
        end

        #100;
        // Test case 4: a=128, b=128, cin=0 → sum=0, cout=1
        a = 8'd128; b = 8'd128; cin = 1'b0;
        #10;
        if (sum !== 8'd0 || cout !== 1'b1) begin
            $display("FAIL: Test case 4 - Expected sum=0, cout=1, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test case 4 - sum=0, cout=1");
        end

        #100;
        // Test case 5: a=100, b=150, cin=1 → sum=251, cout=0
        a = 8'd100; b = 8'd150; cin = 1'b1;
        #10;
        if (sum !== 8'd251 || cout !== 1'b0) begin
            $display("FAIL: Test case 5 - Expected sum=251, cout=0, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test case 5 - sum=251, cout=0");
        end

        #500;
        $display("Simulation completed.");
        $finish;
    end

    always #5 clk = ~clk;

    initial begin
        $monitor("Time=%0t | a=%0d, b=%0d, cin=%b | sum=%0d, cout=%b", $time, a, b, cin, sum, cout);
    end

endmodule