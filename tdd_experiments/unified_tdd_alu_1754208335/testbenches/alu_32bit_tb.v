`timescale 1ns / 1ps

module tb_alu_32bit;

    reg [31:0] a;
    reg [31:0] b;
    reg [3:0] op;
    wire [31:0] result;
    wire zero;

    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );

    reg clk;
    reg rst;

    initial begin
        $dumpfile("tb_alu_32bit.vcd");
        $dumpvars(0, tb_alu_32bit);

        clk = 0;
        rst = 1;
        #20 rst = 0;

        #100; // Wait for reset to settle

        // Test ADD: a=5, b=3, op=4'b0000 → result=8, zero=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0000;
        #10;
        if (result !== 32'd8 || zero !== 1'b0) begin
            $display("FAIL: ADD test failed. Expected 8, got %d, zero=%b", result, zero);
        end else begin
            $display("PASS: ADD test passed. result=%d, zero=%b", result, zero);
        end

        // Test SUB: a=5, b=3, op=4'b0001 → result=2, zero=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0001;
        #10;
        if (result !== 32'd2 || zero !== 1'b0) begin
            $display("FAIL: SUB test failed. Expected 2, got %d, zero=%b", result, zero);
        end else begin
            $display("PASS: SUB test passed. result=%d, zero=%b", result, zero);
        end

        // Test AND: a=5, b=3, op=4'b0010 → result=1, zero=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0010;
        #10;
        if (result !== 32'd1 || zero !== 1'b0) begin
            $display("FAIL: AND test failed. Expected 1, got %d, zero=%b", result, zero);
        end else begin
            $display("PASS: AND test passed. result=%d, zero=%b", result, zero);
        end

        // Test OR: a=5, b=3, op=4'b0011 → result=7, zero=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0011;
        #10;
        if (result !== 32'd7 || zero !== 1'b0) begin
            $display("FAIL: OR test failed. Expected 7, got %d, zero=%b", result, zero);
        end else begin
            $display("PASS: OR test passed. result=%d, zero=%b", result, zero);
        end

        // Test XOR: a=5, b=3, op=4'b0100 → result=6, zero=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0100;
        #10;
        if (result !== 32'd6 || zero !== 1'b0) begin
            $display("FAIL: XOR test failed. Expected 6, got %d, zero=%b", result, zero);
        end else begin
            $display("PASS: XOR test passed. result=%d, zero=%b", result, zero);
        end

        // Test SLL: a=1, b=2, op=4'b0101 → result=4, zero=0
        a = 32'd1;
        b = 32'd2;
        op = 4'b0101;
        #10;
        if (result !== 32'd4 || zero !== 1'b0) begin
            $display("FAIL: SLL test failed. Expected 4, got %d, zero=%b", result, zero);
        end else begin
            $display("PASS: SLL test passed. result=%d, zero=%b", result, zero);
        end

        // Test SRL: a=4, b=2, op=4'b0110 → result=1, zero=0
        a = 32'd4;
        b = 32'd2;
        op = 4'b0110;
        #10;
        if (result !== 32'd1 || zero !== 1'b0) begin
            $display("FAIL: SRL test failed. Expected 1, got %d, zero=%b", result, zero);
        end else begin
            $display("PASS: SRL test passed. result=%d, zero=%b", result, zero);
        end

        // Test invalid op: op=4'b1111 → result=0, zero=1
        a = 32'd5;
        b = 32'd3;
        op = 4'b1111;
        #10;
        if (result !== 32'd0 || zero !== 1'b1) begin
            $display("FAIL: Invalid op test failed. Expected 0, zero=1, got result=%d, zero=%b", result, zero);
        end else begin
            $display("PASS: Invalid op test passed. result=%d, zero=%b", result, zero);
        end

        // Test zero result: a=0, b=0, any valid op → zero=1
        a = 32'd0;
        b = 32'd0;
        op = 4'b0000; // ADD
        #10;
        if (zero !== 1'b1) begin
            $display("FAIL: Zero result test failed. Expected zero=1, got zero=%b", zero);
        end else begin
            $display("PASS: Zero result test passed. zero=%b", zero);
        end

        // Additional random tests over time
        repeat(100) begin
            a = $random;
            b = $random;
            op = $random[3:0];
            #10;
            $monitor("%t | a=%d, b=%d, op=%b, result=%d, zero=%b", $time, a, b, op, result, zero);
        end

        #100;
        $display("Simulation completed.");
        $finish;
    end

    always #5 clk = ~clk;

endmodule