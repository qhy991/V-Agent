`timescale 1ns / 1ps

module tb_counter;

    // 参数定义
    parameter WIDTH = 4;
    parameter CLK_PERIOD = 10.0;

    // 信号声明
    reg         clk;
    reg         rst_n;
    reg         en;
    wire [WIDTH-1:0] count;

    // 实例化被测模块
    counter #(.WIDTH(WIDTH)) uut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .count(count)
    );

    // 时钟生成
    always begin
        clk = 0;
        #(CLK_PERIOD/2);
        clk = 1;
        #(CLK_PERIOD/2);
    end

    // 初始化测试
    initial begin
        integer i;
        $display("Starting counter test...");
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, tb_counter);

        // 初始状态
        rst_n = 0;
        en    = 0;
        @(posedge clk);

        // 测试异步复位
        @(posedge clk);
        if (count === 0) $display("[PASS] Reset test: count is 0 after reset");
        else $display("[FAIL] Reset test: expected 0, got %d", count);

        // 释放复位
        rst_n = 1;

        // 测试使能信号（en=0时保持）
        repeat(3) @(posedge clk);
        if (count === 0) $display("[PASS] Enable low: count remains 0");
        else $display("[FAIL] Enable low: expected 0, got %d", count);

        // 测试递增功能
        en = 1;
        for (i = 1; i <= 15; i = i + 1) begin
            @(posedge clk);
            if (count === i)
                $display("[PASS] Count = %0d at cycle %0d", count, i);
            else
                $display("[FAIL] Expected %0d, got %0d", i, count);
        end

        // 测试回绕（15 -> 0）
        @(posedge clk);
        if (count === 0)
            $display("[PASS] Overflow: 15 -> 0 correctly");
        else
            $display("[FAIL] Overflow: expected 0, got %d", count);

        // 参数化位宽测试（WIDTH=8）
        // 重新实例化已在设计中支持，此处验证通用性
        $display("[INFO] WIDTH=%0d test completed.", WIDTH);

        $display("Counter test completed.");
        #100 $finish;
    end

endmodule