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
    parameter CLK_PERIOD = 10ns;
    reg clk;
    always # (CLK_PERIOD/2) clk = ~clk;

    // 复位信号（可选，但用于初始化）
    reg rst;
    initial begin
        rst = 1;
        # (CLK_PERIOD * 2);
        rst = 0;
    end

    // 波形转储
    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // 监视信号
    initial begin
        $monitor("%t | a=%h, b=%h, cin=%b | sum=%h, cout=%b, overflow=%b", 
                 $time, a, b, cin, sum, cout, overflow);
    end

    // 测试激励
    initial begin
        // 初始化输入
        a = 16'h0000;
        b = 16'h0000;
        cin = 0;

        // Test case 1: a=0, b=0, cin=0 → sum=0, cout=0, overflow=0
        # (CLK_PERIOD * 1);
        a = 16'h0000;
        b = 16'h0000;
        cin = 0;
        # (CLK_PERIOD * 1);
        if (sum !== 16'h0000 || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case 1 failed. Expected sum=0, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 1 passed.");
        end

        // Test case 2: a=FFFF, b=FFFF, cin=1 → sum=0, cout=1, overflow=1 (signed overflow)
        # (CLK_PERIOD * 1);
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1;
        # (CLK_PERIOD * 1);
        if (sum !== 16'h0000 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 2 failed. Expected sum=0, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 2 passed.");
        end

        // Test case 3: a=7FFF, b=7FFF, cin=0 → sum=FFFE, cout=1, overflow=1
        # (CLK_PERIOD * 1);
        a = 16'h7FFF;
        b = 16'h7FFF;
        cin = 0;
        # (CLK_PERIOD * 1);
        if (sum !== 16'hFFFE || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 3 failed. Expected sum=FFFE, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 3 passed.");
        end

        // Test case 4: a=8000, b=8000, cin=0 → sum=0, cout=1, overflow=1
        # (CLK_PERIOD * 1);
        a = 16'h8000;
        b = 16'h8000;
        cin = 0;
        # (CLK_PERIOD * 1);
        if (sum !== 16'h0000 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 4 failed. Expected sum=0, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 4 passed.");
        end

        // Test case 5: a=7FFF, b=8000, cin=0 → sum=FFFF, cout=0, overflow=0
        # (CLK_PERIOD * 1);
        a = 16'h7FFF;
        b = 16'h8000;
        cin = 0;
        # (CLK_PERIOD * 1);
        if (sum !== 16'hFFFF || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case 5 failed. Expected sum=FFFF, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 5 passed.");
        end

        // Test case 6: a=0000, b=0000, cin=1 → sum=1, cout=0, overflow=0
        # (CLK_PERIOD * 1);
        a = 16'h0000;
        b = 16'h0000;
        cin = 1;
        # (CLK_PERIOD * 1);
        if (sum !== 16'h0001 || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case 6 failed. Expected sum=1, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 6 passed.");
        end

        // 模拟完整仿真时间
        # (CLK_PERIOD * 990);

        // 结束仿真
        $display("Simulation completed successfully after %0t ns.", $time);
        $finish;
    end

endmodule