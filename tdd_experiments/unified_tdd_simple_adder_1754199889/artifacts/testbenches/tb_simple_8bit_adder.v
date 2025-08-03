module tb_simple_8bit_adder;

    reg  [7:0] a, b;
    reg         cin;
    wire [7:0] sum;
    wire        cout;

    // 实例化被测模块
    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    initial begin
        $dumpfile("tb_simple_8bit_adder.vcd");
        $dumpvars(0, tb_simple_8bit_adder);

        // 测试用例1: 全零
        a = 8'd0; b = 8'd0; cin = 1'b0;
        #10;
        if (sum !== 8'd0 || cout !== 1'b0) $display("Test 1 Failed: Expected sum=0, cout=0");
        else $display("Test 1 Passed");

        // 测试用例2: 最大值 + 0 + 0
        a = 8'd255; b = 8'd0; cin = 1'b0;
        #10;
        if (sum !== 8'd255 || cout !== 1'b0) $display("Test 2 Failed: Expected sum=255, cout=0");
        else $display("Test 2 Passed");

        // 测试用例3: 最大值 + 0 + 1
        a = 8'd255; b = 8'd0; cin = 1'b1;
        #10;
        if (sum !== 8'd0 || cout !== 1'b1) $display("Test 3 Failed: Expected sum=0, cout=1");
        else $display("Test 3 Passed");

        // 测试用例4: 128 + 128 + 0
        a = 8'd128; b = 8'd128; cin = 1'b0;
        #10;
        if (sum !== 8'd0 || cout !== 1'b1) $display("Test 4 Failed: Expected sum=0, cout=1");
        else $display("Test 4 Passed");

        // 测试用例5: 100 + 150 + 1
        a = 8'd100; b = 8'd150; cin = 1'b1;
        #10;
        if (sum !== 8'd251 || cout !== 1'b0) $display("Test 5 Failed: Expected sum=251, cout=0");
        else $display("Test 5 Passed");

        $finish;
    end

endmodule