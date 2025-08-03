`timescale 1ns / 1ps

module tb_alu_32bit;

    reg [31:0] a;
    reg [31:0] b;
    reg [3:0] op;
    wire [31:0] result;
    wire zero;
    wire overflow;

    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero),
        .overflow(overflow)
    );

    reg clk = 0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("tb_alu_32bit.vcd");
        $dumpvars(0, tb_alu_32bit);

        // Initialize inputs
        a = 0;
        b = 0;
        op = 4'b0000;

        // Wait for reset to complete
        #20;

        // Test ADD: a=5, b=3, op=4'b0000 → result=8, zero=0, overflow=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0000;
        #10;
        if (result !== 32'd8 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: ADD test failed. Expected result=8, got %d", result);
        end else begin
            $display("PASS: ADD test passed.");
        end

        // Test SUB: a=5, b=3, op=4'b0001 → result=2, zero=0, overflow=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0001;
        #10;
        if (result !== 32'd2 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: SUB test failed. Expected result=2, got %d", result);
        end else begin
            $display("PASS: SUB test passed.");
        end

        // Test AND: a=5, b=3, op=4'b0010 → result=1, zero=0, overflow=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0010;
        #10;
        if (result !== 32'd1 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: AND test failed. Expected result=1, got %d", result);
        end else begin
            $display("PASS: AND test passed.");
        end

        // Test OR: a=5, b=3, op=4'b0011 → result=7, zero=0, overflow=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0011;
        #10;
        if (result !== 32'd7 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: OR test failed. Expected result=7, got %d", result);
        end else begin
            $display("PASS: OR test passed.");
        end

        // Test XOR: a=5, b=3, op=4'b0100 → result=6, zero=0, overflow=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b0100;
        #10;
        if (result !== 32'd6 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: XOR test failed. Expected result=6, got %d", result);
        end else begin
            $display("PASS: XOR test passed.");
        end

        // Test NOT: a=5, op=4'b0101 → result=~5, zero=0, overflow=0
        a = 32'd5;
        b = 32'd0; // b not used in NOT
        op = 4'b0101;
        #10;
        if (result !== 32'd'11111111111111111111111111111010 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: NOT test failed. Expected result=~5, got %d", result);
        end else begin
            $display("PASS: NOT test passed.");
        end

        // Test EQ: a=5, b=5, op=4'b0110 → result=1, zero=0, overflow=0
        a = 32'd5;
        b = 32'd5;
        op = 4'b0110;
        #10;
        if (result !== 32'd1 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: EQ test failed. Expected result=1, got %d", result);
        end else begin
            $display("PASS: EQ test passed.");
        end

        // Test LT: a=3, b=5, op=4'b0111 → result=1, zero=0, overflow=0
        a = 32'd3;
        b = 32'd5;
        op = 4'b0111;
        #10;
        if (result !== 32'd1 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: LT test failed. Expected result=1, got %d", result);
        end else begin
            $display("PASS: LT test passed.");
        end

        // Test GT: a=5, b=3, op=4'b1000 → result=1, zero=0, overflow=0
        a = 32'd5;
        b = 32'd3;
        op = 4'b1000;
        #10;
        if (result !== 32'd1 || zero !== 1'b0 || overflow !== 1'b0) begin
            $display("FAIL: GT test failed. Expected result=1, got %d", result);
        end else begin
            $display("PASS: GT test passed.");
        end

        // Test overflow in ADD: a=2147483647, b=1, op=4'b0000 → result=-2147483648, overflow=1
        a = 32'd2147483647;
        b = 32'd1;
        op = 4'b0000;
        #10;
        if (result !== 32'd-2147483648 || zero !== 1'b0 || overflow !== 1'b1) begin
            $display("FAIL: Overflow ADD test failed. Expected result=-2147483648, overflow=1, got result=%d, overflow=%b", result, overflow);
        end else begin
            $display("PASS: Overflow ADD test passed.");
        end

        // Final simulation end
        #100;
        $display("Simulation completed.");
        $finish;
    end

    initial begin
        $monitor("Time: %0t | a=%0d, b=%0d, op=%b | result=%0d, zero=%b, overflow=%b", $time, a, b, op, result, zero, overflow);
    end

endmodule