`timescale 1ns / 1ps

module tb_simple_8bit_adder;

    reg [7:0] a;
    reg [7:0] b;
    reg       cin;
    wire [7:0] sum;
    wire       cout;

    // 实例化被测模块
    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    // 时钟生成
    parameter CLK_PERIOD = 10;
    reg clk;
    always # (CLK_PERIOD/2) clk = ~clk;

    // 测试激励
    initial begin
        $dumpfile("tb_simple_8bit_adder.vcd");
        $dumpvars(0, tb_simple_8bit_adder);

        // 初始化信号
        a = 8'd0;
        b = 8'd0;
        cin = 1'b0;

        // 显示初始状态
        $display("Time\tA\tB\tCin\tSum\tCout\tExpected Sum\tExpected Cout");
        $monitor("%0t\t%0d\t%0d\t%0b\t%0d\t%0b\t%0d\t%0b", $time, a, b, cin, sum, cout, sum, cout);

        // 测试用例1: a=0, b=0, cin=0 → sum=0, cout=0
        #100;
        a = 8'd0; b = 8'd0; cin = 1'b0;
        #10;
        if (sum !== 8'd0 || cout !== 1'b0) begin
            $error("Test case 1 failed: expected sum=0, cout=0, got sum=%0d, cout=%0b", sum, cout);
        end else begin
            $display("Test case 1 passed: a=0, b=0, cin=0 → sum=0, cout=0");
        end

        // 测试用例2: a=255, b=0, cin=0 → sum=255, cout=0
        #100;
        a = 8'd255; b = 8'd0; cin = 1'b0;
        #10;
        if (sum !== 8'd255 || cout !== 1'b0) begin
            $error("Test case 2 failed: expected sum=255, cout=0, got sum=%0d, cout=%0b", sum, cout);
        end else begin
            $display("Test case 2 passed: a=255, b=0, cin=0 → sum=255, cout=0");
        end

        // 测试用例3: a=255, b=0, cin=1 → sum=0, cout=1
        #100;
        a = 8'd255; b = 8'd0; cin = 1'b1;
        #10;
        if (sum !== 8'd0 || cout !== 1'b1) begin
            $error("Test case 3 failed: expected sum=0, cout=1, got sum=%0d, cout=%0b", sum, cout);
        end else begin
            $display("Test case 3 passed: a=255, b=0, cin=1 → sum=0, cout=1");
        end

        // 测试用例4: a=128, b=127, cin=1 → sum=256 → sum=0, cout=1
        #100;
        a = 8'd128; b = 8'd127; cin = 1'b1;
        #10;
        if (sum !== 8'd0 || cout !== 1'b1) begin
            $error("Test case 4 failed: expected sum=0, cout=1, got sum=%0d, cout=%0b", sum, cout);
        end else begin
            $display("Test case 4 passed: a=128, b=127, cin=1 → sum=0, cout=1");
        end

        // 测试用例5: a=127, b=127, cin=1 → sum=255, cout=0
        #100;
        a = 8'd127; b = 8'd127; cin = 1'b1;
        #10;
        if (sum !== 8'd255 || cout !== 1'b0) begin
            $error("Test case 5 failed: expected sum=255, cout=0, got sum=%0d, cout=%0b", sum, cout);
        end else begin
            $display("Test case 5 passed: a=127, b=127, cin=1 → sum=255, cout=0");
        end

        // 测试用例6: a=128, b=128, cin=0 → sum=0, cout=1
        #100;
        a = 8'd128; b = 8'd128; cin = 1'b0;
        #10;
        if (sum !== 8'd0 || cout !== 1'b1) begin
            $error("Test case 6 failed: expected sum=0, cout=1, got sum=%0d, cout=%0b", sum, cout);
        end else begin
            $display("Test case 6 passed: a=128, b=128, cin=0 → sum=0, cout=1");
        end

        // 仿真结束
        #100;
        $display("All test cases completed.");
        $finish;
    end

endmodule