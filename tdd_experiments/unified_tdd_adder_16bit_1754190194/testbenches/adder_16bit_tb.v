`timescale 1ns / 1ps

module tb_adder_16bit;

    // 信号声明
    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire       cout;
    wire       overflow;

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
    parameter CLK_PERIOD = 10;
    reg clk;
    always # (CLK_PERIOD/2) clk = ~clk;

    // 复位生成（可选，用于初始化）
    initial begin
        clk = 0;
        #10;
    end

    // 波形转储设置
    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // 测试激励与结果检查
    initial begin
        // 初始化输入
        a = 0;
        b = 0;
        cin = 0;

        // 显示初始状态
        $display("Time\tA\t\tB\t\tCin\tSum\t\tCout\tOverflow");
        $monitor("%0t\t%5d\t%5d\t%1d\t%5d\t%1d\t%1d", $time, a, b, cin, sum, cout, overflow);

        // 测试场景1：正数相加，触发溢出
        #100;
        a = 16'd32767;  // 最大正数
        b = 16'd1;
        cin = 0;
        #100;
        if (sum !== 16'd-32768 || cout !== 1'b0 || overflow !== 1'b1) begin
            $error("Test 1 failed: Expected sum=-32768, cout=0, overflow=1, got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test 1 passed: Positive overflow detected.");
        end

        // 测试场景2：负数相加，触发溢出
        #100;
        a = 16'd-32768; // 最小负数
        b = 16'd-1;
        cin = 0;
        #100;
        if (sum !== 16'd32767 || cout !== 1'b0 || overflow !== 1'b1) begin
            $error("Test 2 failed: Expected sum=32767, cout=0, overflow=1, got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test 2 passed: Negative overflow detected.");
        end

        // 测试场景3：正数 + 负数，无溢出
        #100;
        a = 16'd1000;
        b = 16'd-500;
        cin = 0;
        #100;
        if (sum !== 16'd500 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 3 failed: Expected sum=500, cout=0, overflow=0, got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test 3 passed: Mixed sign addition within range.");
        end

        // 测试场景4：最大值加法
        #100;
        a = 16'hFFFF;
        b = 16'h0000;
        cin = 0;
        #100;
        if (sum !== 16'hFFFF || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 4 failed: Expected sum=16'hFFFF, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test 4 passed: Max value addition.");
        end

        // 测试场景5：进位传播
        #100;
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 0;
        #100;
        if (sum !== 16'h0000 || cout !== 1'b1 || overflow !== 1'b0) begin
            $error("Test 5 failed: Expected sum=0, cout=1, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test 5 passed: Carry propagation test.");
        end

        // 测试场景6：边界情况：a=0, b=0, cin=1
        #100;
        a = 0;
        b = 0;
        cin = 1;
        #100;
        if (sum !== 1 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 6 failed: Expected sum=1, cout=0, overflow=0, got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test 6 passed: Cin=1 with zero inputs.");
        end

        // 测试场景7：零值
        #100;
        a = 0;
        b = 0;
        cin = 0;
        #100;
        if (sum !== 0 || cout !== 1'b0 || overflow !== 1'b0) begin
            $error("Test 7 failed: Expected sum=0, cout=0, overflow=0, got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test 7 passed: Zero input test.");
        end

        // 仿真结束
        #100;
        $display("All tests completed.");
        $finish;
    end

endmodule