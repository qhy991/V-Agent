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
    reg clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // 复位信号（可选，但用于初始化）
    reg rst = 1;
    initial begin
        #20 rst = 0;
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

        // 等待复位释放
        @(posedge clk);

        // 测试场景1: 最大值相加，应溢出且进位为1
        $display("=== Test Case 1: Max value addition (a=FFFF, b=FFFF, cin=1) ===");
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1;
        @(posedge clk);
        #10;
        if (sum !== 16'hFFFE || cout !== 1 || overflow !== 1) begin
            $error("Test Case 1 Failed: Expected sum=FFFE, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test Case 1 Passed");
        end

        // 测试场景2: 最小值相加，无进位，无溢出
        $display("=== Test Case 2: Min value addition (a=0000, b=0000, cin=0) ===");
        a = 16'h0000;
        b = 16'h0000;
        cin = 0;
        @(posedge clk);
        #10;
        if (sum !== 16'h0000 || cout !== 0 || overflow !== 0) begin
            $error("Test Case 2 Failed: Expected sum=0000, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test Case 2 Passed");
        end

        // 测试场景3: 正数相加不溢出
        $display("=== Test Case 3: Positive add without overflow (a=7FFF, b=0001, cin=0) ===");
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 0;
        @(posedge clk);
        #10;
        if (sum !== 16'h8000 || cout !== 0 || overflow !== 0) begin
            $error("Test Case 3 Failed: Expected sum=8000, cout=0, overflow=0, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test Case 3 Passed");
        end

        // 测试场景4: 负数相加溢出（两个最小负数相加）
        $display("=== Test Case 4: Negative add with overflow (a=8000, b=8000, cin=0) ===");
        a = 16'h8000;
        b = 16'h8000;
        cin = 0;
        @(posedge clk);
        #10;
        if (sum !== 16'h0000 || cout !== 1 || overflow !== 1) begin
            $error("Test Case 4 Failed: Expected sum=0000, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test Case 4 Passed");
        end

        // 测试场景5: 边界情况，进位传播测试
        $display("=== Test Case 5: Boundary case with carry propagation (a=7FFF, b=0001, cin=1) ===");
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1;
        @(posedge clk);
        #10;
        if (sum !== 16'h8000 || cout !== 1 || overflow !== 1) begin
            $error("Test Case 5 Failed: Expected sum=8000, cout=1, overflow=1, got sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("Test Case 5 Passed");
        end

        // 完成所有测试
        $display("All test cases completed.");
        #100;
        $finish;
    end

endmodule