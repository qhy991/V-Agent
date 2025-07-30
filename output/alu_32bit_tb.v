`timescale 1ns/1ps

module alu_32bit_tb();
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

    initial begin
        $monitor("Time %0t: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x, zero=%b, overflow=%b", $time, a, b, op, result, zero, overflow);

        // Test case 1: ADD
        a = 32'h12345678;
        b = 32'h87654321;
        op = 4'b0000;
        #10;

        // Test case 2: SUB
        a = 32'h12345678;
        b = 32'h87654321;
        op = 4'b0001;
        #10;

        // Test case 3: AND
        a = 32'h12345678;
        b = 32'h87654321;
        op = 4'b0010;
        #10;

        // Test case 4: OR
        a = 32'h12345678;
        b = 32'h87654321;
        op = 4'b0011;
        #10;

        // Test case 5: XOR
        a = 32'h12345678;
        b = 32'h87654321;
        op = 4'b0100;
        #10;

        // Test case 6: NOT
        a = 32'h12345678;
        b = 32'h00000000;
        op = 4'b0101;
        #10;

        // Test case 7: Default case
        a = 32'h12345678;
        b = 32'h87654321;
        op = 4'b1111;
        #10;

        $finish;
    end
endmodule