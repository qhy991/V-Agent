module alu_tb;

    reg [31:0] a;
    reg [31:0] b;
    reg [3:0] op;
    wire [31:0] result;

    // Instantiate the DUT
    alu uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result)
    );

    initial begin
        $dumpfile("alu_tb.vcd");
        $dumpvars(0, alu_tb);

        // Test case 1: Add
        a = 32'h00000001;
        b = 32'h00000002;
        op = 4'b0000;
        #10;
        $display("Test Case 1 - ADD: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 2: Subtract
        a = 32'h00000005;
        b = 32'h00000003;
        op = 4'b0001;
        #10;
        $display("Test Case 2 - SUB: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 3: AND
        a = 32'h000000FF;
        b = 32'h000000AA;
        op = 4'b0010;
        #10;
        $display("Test Case 3 - AND: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 4: OR
        a = 32'h000000AA;
        b = 32'h00000055;
        op = 4'b0011;
        #10;
        $display("Test Case 4 - OR: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 5: XOR
        a = 32'h000000FF;
        b = 32'h000000AA;
        op = 4'b0100;
        #10;
        $display("Test Case 5 - XOR: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 6: Default (invalid op code)
        a = 32'h00000000;
        b = 32'h00000000;
        op = 4'b1111;
        #10;
        $display("Test Case 6 - Default: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 7: Boundary values (max and min)
        a = 32'hFFFFFFFF;
        b = 32'h00000000;
        op = 4'b0000;
        #10;
        $display("Test Case 7 - ADD (Max): a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 8: Random values
        a = 32'hA1B2C3D4;
        b = 32'h12345678;
        op = 4'b0010;
        #10;
        $display("Test Case 8 - Random: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 9: Overflow test (Addition)
        a = 32'h7FFFFFFF;
        b = 32'h00000001;
        op = 4'b0000;
        #10;
        $display("Test Case 9 - ADD Overflow: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        // Test case 10: Underflow test (Subtraction)
        a = 32'h00000000;
        b = 32'h00000001;
        op = 4'b0001;
        #10;
        $display("Test Case 10 - SUB Underflow: a=0x%08x, b=0x%08x, op=0x%01x, result=0x%08x", a, b, op, result);

        $finish;
    end

endmodule