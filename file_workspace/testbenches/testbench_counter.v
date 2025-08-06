`timescale 1ns / 1ps

module tb_counter;

    // 信号声明
    reg clk;
    reg rst_n;
    reg en;
    wire [7:0] count;

    // 测试计数器变量
    integer passed_count = 0;
    integer failed_count = 0;
    integer total_count = 0;

    // 被测模块实例化
    counter uut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .count(count)
    );

    // 时钟生成：周期 10.0ns
    always begin
        #5 clk = ~clk;  // 5ns 高电平，5ns 低电平 → 周期=10ns
    end

    // 初始化复位和使能
    initial begin
        clk = 0;
        rst_n = 0;
        en = 0;

        // 波形转储设置（可选，用于仿真工具查看波形）
        $dumpfile("counter.vcd");
        $dumpvars(0, tb_counter);

        // 初始等待稳定
        #100;

        // === 测试用例 1: reset_release_timing ===
        total_count = total_count + 1;
        $display("Time=%0t: Test Case %0d - %s", $time, total_count, "reset_release_timing");
        rst_n = 0;
        en = 0;
        #20;  // 复位保持两个周期
        rst_n = 1;
        #10;  // 释放复位
        if (count != 8'h0) begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h0, count, "FAIL");
            failed_count = failed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'h0, count, "PASS");
            passed_count = passed_count + 1;
        end

        // === 测试用例 2: enable_toggle ===
        total_count = total_count + 1;
        $display("Time=%0t: Test Case %0d - %s", $time, total_count, "enable_toggle");
        en = 1;
        #10;
        if (count != 8'h1) begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h1, count, "FAIL");
            failed_count = failed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'h1, count, "PASS");
            passed_count = passed_count + 1;
        end
        en = 0;
        #10;
        if (count != 8'h1) begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h1, count, "FAIL");
            failed_count = failed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'h1, count, "PASS");
            passed_count = passed_count + 1;
        end

        // === 测试用例 3: boundary_values ===
        total_count = total_count + 1;
        $display("Time=%0t: Test Case %0d - %s", $time, total_count, "boundary_values");
        en = 1;
        for (integer i = 0; i < 255; i = i + 1) begin
            #10;
        end
        if (count != 8'hFF) begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'hFF, count, "FAIL");
            failed_count = failed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'hFF, count, "PASS");
            passed_count = passed_count + 1;
        end
        en = 0;
        #10;
        if (count != 8'hFF) begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'hFF, count, "FAIL");
            failed_count = failed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'hFF, count, "PASS");
            passed_count = passed_count + 1;
        end

        // === 测试用例 4: multi_cycle_hold ===
        total_count = total_count + 1;
        $display("Time=%0t: Test Case %0d - %s", $time, total_count, "multi_cycle_hold");
        en = 1;
        #10;
        if (count != 8'h0) begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h0, count, "FAIL");
            failed_count = failed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'h0, count, "PASS");
            passed_count = passed_count + 1;
        end
        en = 0;
        for (integer i = 0; i < 10; i = i + 1) begin
            #10;
        end
        if (count != 8'h0) begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h0, count, "FAIL");
            failed_count = failed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'h0, count, "PASS");
            passed_count = passed_count + 1;
        end

        // 最终统计输出
        $display("==================================================");
        $display("Test Summary:");
        $display("Total Tests: %0d", total_count);
        $display("Passed: %0d", passed_count);
        $display("Failed: %0d", failed_count);
        $display("==================================================");
        if (failed_count == 0) begin
            $display("All passed!");
        end
        $display("==================================================");

        // 结束仿真
        #100;
        $finish;
    end

endmodule