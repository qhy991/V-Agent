`timescale 1ns / 1ps

module tb_adder_16bit;

    // 定义时钟周期
    parameter CLK_PERIOD = 10.0;

    // 信号声明
    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // 时钟和复位信号
    reg clk;
    reg rst_n;

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
    always begin
        # (CLK_PERIOD / 2) clk = ~clk;
    end

    // 复位生成
    initial begin
        clk = 0;
        rst_n = 0;
        # (CLK_PERIOD * 2);
        rst_n = 1;
    end

    // 波形转储设置（VCD文件）
    initial begin
        $dumpfile("tb_adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // 测试场景定义
    integer i;

    // 基本加法测试
    initial begin
        $display("=== Basic Test ===");
        a = 16'h0000; b = 16'h0000; cin = 0;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x0000, b=0x0000, cin=0 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);

        a = 16'h0001; b = 16'h0002; cin = 0;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x0001, b=0x0002, cin=0 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);

        a = 16'h00FF; b = 16'h0001; cin = 0;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x00FF, b=0x0001, cin=0 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);
    end

    // 进位传播测试
    initial begin
        $display("=== Carry Propagation Test ===");
        a = 16'h0000; b = 16'h0000; cin = 1;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x0000, b=0x0000, cin=1 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);

        a = 16'h0000; b = 16'h0000; cin = 1;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x0000, b=0x0000, cin=1 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);

        a = 16'h0000; b = 16'h0000; cin = 1;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x0000, b=0x0000, cin=1 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);
    end

    // 溢出检测测试
    initial begin
        $display("=== Overflow Test ===");
        a = 16'h8000; b = 16'h8000; cin = 0;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x8000, b=0x8000, cin=0 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);

        a = 16'h7FFF; b = 16'h7FFF; cin = 0;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x7FFF, b=0x7FFF, cin=0 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);

        a = 16'h7FFF; b = 16'h0001; cin = 0;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x7FFF, b=0x0001, cin=0 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);
    end

    // 边界值测试
    initial begin
        $display("=== Boundary Value Test ===");
        a = 16'h0000; b = 16'h0000; cin = 0;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x0000, b=0x0000, cin=0 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);

        a = 16'hFFFF; b = 16'hFFFF; cin = 0;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0xFFFF, b=0xFFFF, cin=0 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);

        a = 16'h0000; b = 16'hFFFF; cin = 1;
        # (CLK_PERIOD * 2);
        $display("Test case: a=0x0000, b=0xFFFF, cin=1 => sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);
    end

    // 随机数据测试
    initial begin
        $display("=== Random Data Test ===");
        for (i = 0; i < 100; i = i + 1) begin
            a = $random % 65536;
            b = $random % 65536;
            cin = $random % 2;
            # (CLK_PERIOD * 2);
            $display("Test case: a=0x%04X, b=0x%04X, cin=%b => sum=0x%04X, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);
        end
    end

    // 结果检查和断言
    initial begin
        # (CLK_PERIOD * 200); // 等待所有测试完成
        $display("=== Test Completed ===");
        $finish;
    end

    // 监视器输出
    initial begin
        $monitor("Time: %t | a=0x%04X | b=0x%04X | cin=%b | sum=0x%04X | cout=%b | overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule