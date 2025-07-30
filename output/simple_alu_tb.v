module simple_alu_tb;

    // Inputs
    reg [3:0] a;
    reg [3:0] b;
    reg [1:0] op;

    // Outputs
    wire [3:0] result;
    wire zero_flag;

    // Instantiate the Unit Under Test (UUT)
    simple_alu uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero_flag(zero_flag)
    );

    initial begin
        $dumpfile("simple_alu_tb.vcd");
        $dumpvars(0, simple_alu_tb);

        // Test case 1: Add 0 and 0
        a = 4'b0000;
        b = 4'b0000;
        op = 2'b00;
        #10;
        $display("Test Case 1: a=0, b=0, op=ADD -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 2: Add 1 and 1
        a = 4'b0001;
        b = 4'b0001;
        op = 2'b00;
        #10;
        $display("Test Case 2: a=1, b=1, op=ADD -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 3: Subtract 0 from 0
        a = 4'b0000;
        b = 4'b0000;
        op = 2'b01;
        #10;
        $display("Test Case 3: a=0, b=0, op=SUB -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 4: Subtract 1 from 1
        a = 4'b0001;
        b = 4'b0001;
        op = 2'b01;
        #10;
        $display("Test Case 4: a=1, b=1, op=SUB -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 5: AND 0 and 0
        a = 4'b0000;
        b = 4'b0000;
        op = 2'b10;
        #10;
        $display("Test Case 5: a=0, b=0, op=AND -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 6: AND 1 and 1
        a = 4'b0001;
        b = 4'b0001;
        op = 2'b10;
        #10;
        $display("Test Case 6: a=1, b=1, op=AND -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 7: OR 0 and 0
        a = 4'b0000;
        b = 4'b0000;
        op = 2'b11;
        #10;
        $display("Test Case 7: a=0, b=0, op=OR -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 8: OR 1 and 1
        a = 4'b0001;
        b = 4'b0001;
        op = 2'b11;
        #10;
        $display("Test Case 8: a=1, b=1, op=OR -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 9: ADD with max values (7 + 7 = 14)
        a = 4'b0111;
        b = 4'b0111;
        op = 2'b00;
        #10;
        $display("Test Case 9: a=7, b=7, op=ADD -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 10: SUB with max values (7 - 0 = 7)
        a = 4'b0111;
        b = 4'b0000;
        op = 2'b01;
        #10;
        $display("Test Case 10: a=7, b=0, op=SUB -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 11: AND with all 1s (15 & 15 = 15)
        a = 4'b1111;
        b = 4'b1111;
        op = 2'b10;
        #10;
        $display("Test Case 11: a=15, b=15, op=AND -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 12: OR with all 1s (15 | 15 = 15)
        a = 4'b1111;
        b = 4'b1111;
        op = 2'b11;
        #10;
        $display("Test Case 12: a=15, b=15, op=OR -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 13: ADD with overflow (8 + 8 = 16, but 4-bit result is 0)
        a = 4'b1000;
        b = 4'b1000;
        op = 2'b00;
        #10;
        $display("Test Case 13: a=8, b=8, op=ADD -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 14: SUB with underflow (0 - 8 = -8, but 4-bit result is 8)
        a = 4'b0000;
        b = 4'b1000;
        op = 2'b01;
        #10;
        $display("Test Case 14: a=0, b=8, op=SUB -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 15: Random test case (a=5, b=3, op=ADD)
        a = 4'b0101;
        b = 4'b0011;
        op = 2'b00;
        #10;
        $display("Test Case 15: a=5, b=3, op=ADD -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 16: Random test case (a=10, b=5, op=SUB)
        a = 4'b1010;
        b = 4'b0101;
        op = 2'b01;
        #10;
        $display("Test Case 16: a=10, b=5, op=SUB -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 17: Random test case (a=3, b=5, op=AND)
        a = 4'b0011;
        b = 4'b0101;
        op = 2'b10;
        #10;
        $display("Test Case 17: a=3, b=5, op=AND -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 18: Random test case (a=12, b=13, op=OR)
        a = 4'b1100;
        b = 4'b1101;
        op = 2'b11;
        #10;
        $display("Test Case 18: a=12, b=13, op=OR -> result=%b, zero_flag=%b", result, zero_flag);

        // Test case 19: Invalid op code (default case)
        a = 4'b0000;
        b = 4'b0000;
        op = 2'b11;
        #10;
        $display("Test Case 19: a=0, b=0, op=INVALID -> result=%b, zero_flag=%b", result, zero_flag);

        // End of simulation
        $finish;
    end

endmodule