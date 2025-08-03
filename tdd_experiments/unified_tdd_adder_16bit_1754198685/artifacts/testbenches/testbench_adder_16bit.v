module tb_adder_16bit;
    reg  [15:0] a, b;
    reg         cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // Instantiate DUT
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Test case 1: zero inputs
        a = 16'd0; b = 16'd0; cin = 1'b0;
        #10;
        $display("Test 1: a=0, b=0, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);

        // Test case 2: max + 1
        a = 16'hFFFF; b = 16'h0001; cin = 1'b0;
        #10;
        $display("Test 2: a=FFFF, b=0001, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);

        // Test case 3: positive overflow
        a = 16'h7FFF; b = 16'h7FFF; cin = 1'b0;
        #10;
        $display("Test 3: a=7FFF, b=7FFF, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);

        // Test case 4: negative overflow
        a = 16'h8000; b = 16'h8000; cin = 1'b0;
        #10;
        $display("Test 4: a=8000, b=8000, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);

        // Test case 5: mixed signs
        a = 16'h7FFF; b = 16'h8000; cin = 1'b0;
        #10;
        $display("Test 5: a=7FFF, b=8000, cin=0 -> sum=%h, cout=%b, overflow=%b", sum, cout, overflow);

        $finish;
    end

endmodule