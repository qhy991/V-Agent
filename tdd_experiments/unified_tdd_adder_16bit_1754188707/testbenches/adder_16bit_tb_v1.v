`timescale 1ns / 1ps

module tb_adder_16bit;

    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // 实例化被测模块
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // 时钟生成
    reg clk = 0;
    always #5 clk = ~clk; // 10ns周期

    // 测试激励
    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // 初始化输入
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;

        // 初始等待
        #20;

        // 测试正数相加：a=16'h0001, b=16'h0002, cin=1'b0 → sum=3, cout=0, overflow=0
        a = 16'h0001;
        b = 16'h0002;
        cin = 1'b0;
        #20;
        $display("Test 1: a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0003 && cout == 1'b0 && overflow == 1'b0) else $error("Test 1 failed");

        // 测试负数相加：a=16'hFFFF, b=16'hFFFF, cin=1'b0 → sum=16'hFFFE, cout=1, overflow=1
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b0;
        #20;
        $display("Test 2: a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'hFFFE && cout == 1'b1 && overflow == 1'b1) else $error("Test 2 failed");

        // 测试最大值相加：a=16'hFFFF, b=16'hFFFF, cin=1'b1 → sum=16'hFFFF, cout=1, overflow=1
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b1;
        #20;
        $display("Test 3: a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'hFFFF && cout == 1'b1 && overflow == 1'b1) else $error("Test 3 failed");

        // 测试边界情况：a=16'h8000, b=16'h8000, cin=1'b0 → sum=16'h0000, cout=1, overflow=1
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #20;
        $display("Test 4: a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h0000 && cout == 1'b1 && overflow == 1'b1) else $error("Test 4 failed");

        // 测试无溢出：a=16'h4000, b=16'h4000, cin=1'b0 → sum=16'h8000, cout=0, overflow=0
        a = 16'h4000;
        b = 16'h4000;
        cin = 1'b0;
        #20;
        $display("Test 5: a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        assert(sum == 16'h8000 && cout == 1'b0 && overflow == 1'b0) else $error("Test 5 failed");

        // 完成仿真
        #20;
        $display("All tests completed.");
        $finish;
    end

    // 监视信号变化
    initial begin
        $monitor("%t | a=16'h%h, b=16'h%h, cin=%b | sum=16'h%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule