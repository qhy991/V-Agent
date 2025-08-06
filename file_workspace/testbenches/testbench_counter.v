`timescale 1ns / 1ps

module counter_tb;

    // 信号声明
    reg clk;
    reg rst_n;
    wire [3:0] count;

    // 测试计数器变量
    integer passed_count;
    integer failed_count;
    integer total_count;
    integer test_number;

    // 被测模块实例化
    counter uut (
        .clk(clk),
        .rst_n(rst_n),
        .count(count)
    );

    // 时钟生成逻辑
    initial begin
        clk = 0;
        forever #5.0 clk = ~clk; // 10ns周期
    end

    // 复位生成逻辑
    initial begin
        rst_n = 0;
        #10.0 rst_n = 1;
    end

    // 波形转储设置
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);
    end

    // 测试用例执行
    initial begin
        // 初始化计数器
        passed_count = 0;
        failed_count = 0;
        total_count = 3; // basic_test, reset_test, rollover_test
        test_number = 1;

        // 基本功能测试 (basic_test)
        $display("==================================================");
        $display("Starting Test Case %0d: basic_test", test_number);
        $display("Time=%0t: Test Case %0d - %s", $time, test_number, "basic_test");

        // 初始状态
        rst_n = 0;
        #10.0 rst_n = 1;

        // 等待几个时钟周期
        #100.0;

        // 检查计数器是否从0开始递增
        if (count === 4'b0000) begin
            $display("Expected: %h, Got: %h, Status: PASS", 4'b0000, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 4'b0000, count);
            failed_count = failed_count + 1;
        end

        $display("Time=%0t: Test Case %0d - %s", $time, test_number, "basic_test");
        $display("Expected: %h, Got: %h, Status: %s", 4'b0000, count, (count === 4'b0000) ? "PASS" : "FAIL");
        test_number = test_number + 1;

        // 复位功能测试 (reset_test)
        $display("==================================================");
        $display("Starting Test Case %0d: reset_test", test_number);
        $display("Time=%0t: Test Case %0d - %s", $time, test_number, "reset_test");

        // 重置计数器
        rst_n = 0;
        #10.0 rst_n = 1;

        // 等待一个时钟周期
        #10.0;

        // 检查复位后是否为0
        if (count === 4'b0000) begin
            $display("Expected: %h, Got: %h, Status: PASS", 4'b0000, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 4'b0000, count);
            failed_count = failed_count + 1;
        end

        $display("Time=%0t: Test Case %0d - %s", $time, test_number, "reset_test");
        $display("Expected: %h, Got: %h, Status: %s", 4'b0000, count, (count === 4'b0000) ? "PASS" : "FAIL");
        test_number = test_number + 1;

        // 溢出测试 (rollover_test)
        $display("==================================================");
        $display("Starting Test Case %0d: rollover_test", test_number);
        $display("Time=%0t: Test Case %0d - %s", $time, test_number, "rollover_test");

        // 等待足够多的时钟周期使计数器溢出
        #100.0;

        // 检查溢出后是否回到0
        if (count === 4'b0000) begin
            $display("Expected: %h, Got: %h, Status: PASS", 4'b0000, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 4'b0000, count);
            failed_count = failed_count + 1;
        end

        $display("Time=%0t: Test Case %0d - %s", $time, test_number, "rollover_test");
        $display("Expected: %h, Got: %h, Status: %s", 4'b0000, count, (count === 4'b0000) ? "PASS" : "FAIL");
        test_number = test_number + 1;

        // 测试结束
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

        $finish;
    end

endmodule