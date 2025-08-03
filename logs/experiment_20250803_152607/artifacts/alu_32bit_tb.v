`timescale 1ns / 1ps

timescale 1ns/1ps

module alu_32bit_tb;
    reg [31:0] a, b;
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
        $dumpfile("alu_32bit.vcd");
        $dumpvars(0, alu_32bit_tb);

        // Test ADD
        a = 32'd5; b = 32'd3; op = 4'b0000; #10;
        assert(result == 32'd8) else $error("ADD failed: expected 8, got %d", result);
        assert(zero == 1'b0) else $error("ADD zero flag incorrect");
        assert(overflow == 1'b0) else $error("ADD overflow incorrect");

        // Test SUB
        a = 32'd5; b = 32'd3; op = 4'b0001; #10;
        assert(result == 32'd2) else $error("SUB failed: expected 2, got %d", result);
        assert(zero == 1'b0) else $error("SUB zero flag incorrect");
        assert(overflow == 1'b0) else $error("SUB overflow incorrect");

        // Test AND
        a = 32'd5; b = 32'd3; op = 4'b0010; #10;
        assert(result == 32'd1) else $error("AND failed: expected 1, got %d", result);
        assert(zero == 1'b0) else $error("AND zero flag incorrect");
        assert(overflow == 1'b0) else $error("AND overflow incorrect");

        // Test OR
        a = 32'd5; b = 32'd3; op = 4'b0011; #10;
        assert(result == 32'd7) else $error("OR failed: expected 7, got %d", result);
        assert(zero == 1'b0) else $error("OR zero flag incorrect");
        assert(overflow == 1'b0) else $error("OR overflow incorrect");

        // Test XOR
        a = 32'd5; b = 32'd3; op = 4'b0100; #10;
        assert(result == 32'd6) else $error("XOR failed: expected 6, got %d", result);
        assert(zero == 1'b0) else $error("XOR zero flag incorrect");
        assert(overflow == 1'b0) else $error("XOR overflow incorrect");

        // Test NOT
        a = 32'd5; b = 32'd0; op = 4'b0101; #10;
        assert(result == 32'd~5) else $error("NOT failed: expected %h, got %h", ~5, result);
        assert(zero == 1'b0) else $error("NOT zero flag incorrect");
        assert(overflow == 1'b0) else $error("NOT overflow incorrect");

        // Test EQ
        a = 32'd5; b = 32'd5; op = 4'b0110; #10;
        assert(result == 32'd1) else $error("EQ failed: expected 1, got %d", result);
        assert(zero == 1'b0) else $error("EQ zero flag incorrect");
        assert(overflow == 1'b0) else $error("EQ overflow incorrect");

        // Test LT
        a = 32'd3; b = 32'd5; op = 4'b0111; #10;
        assert(result == 32'd1) else $error("LT failed: expected 1, got %d", result);
        assert(zero == 1'b0) else $error("LT zero flag incorrect");
        assert(overflow == 1'b0) else $error("LT overflow incorrect");

        // Test GT
        a = 32'd5; b = 32'd3; op = 4'b1000; #10;
        assert(result == 32'd1) else $error("GT failed: expected 1, got %d", result);
        assert(zero == 1'b0) else $error("GT zero flag incorrect");
        assert(overflow == 1'b0) else $error("GT overflow incorrect");

        // Test overflow (positive overflow)
        a = 32'h7FFFFFFF; b = 32'd1; op = 4'b0000; #10;
        assert(result == 32'h80000000) else $error("Overflow ADD failed: expected 80000000, got %h", result);
        assert(overflow == 1'b1) else $error("Overflow flag not set");

        // Test underflow (negative underflow)
        a = 32'h80000000; b = 32'd1; op = 4'b0001; #10;
        assert(result == 32'h7FFFFFFF) else $error("Underflow SUB failed: expected 7FFFFFFF, got %h", result);
        assert(overflow == 1'b1) else $error("Underflow flag not set");

        $display("All tests passed!");
        $finish;
    end

endmodule