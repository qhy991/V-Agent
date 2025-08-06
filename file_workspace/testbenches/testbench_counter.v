`timescale 1ns / 1ps

module counter_tb;

    // 信号声明
    reg clk;
    reg reset;
    wire [3:0] count;

    // 测试计数器变量
    integer passed_count = 0;
    integer failed_count = 0;
    integer total_count = 0;
    integer test_number = 0;

    // 被测模块实例化
    counter uut (
        .clk(clk),
        .reset(reset),
        .count(count)
    );

    // 时钟生成（周期10ns）
    always begin
        #5 clk = ~clk;
    end

    // 初始过程
    initial begin
        // 初始化信号
        clk = 0;
        reset = 1;

        // 波形转储设置
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);

        // 开始测试
        $display("Starting counter_tb simulation...");

        // 测试1: reset_test - 验证复位功能
        test_number = test_number + 1;
        total_count = total_count + 1;

        reset = 1;
        #10; // 等待一个时钟周期

        if (count === 4'b0) begin
            $display("Time=%0t: Test Case %0d - reset_test", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 4'b0, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Time=%0t: Test Case %0d - reset_test", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 4'b0, count);
            failed_count = failed_count + 1;
        end

        // 测试2: counting_test - 验证计数功能
        test_number = test_number + 1;
        total_count = total_count + 1;

        reset = 0;
        #10; // clk 1
        if (count === 4'b0001) begin
            $display("Time=%0t: Test Case %0d - counting_test", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 4'b0001, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Time=%0t: Test Case %0d - counting_test", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 4'b0001, count);
            failed_count = failed_count + 1;
        end

        // 测试3: boundary_test - 验证边界条件（计数到最大值后回0）
        test_number = test_number + 1;
        total_count = total_count + 1;

        // 设置count为最大值
        count = 4'b1110;
        #10; // clk 1 -> count = 4'b1111
        #10; // clk 2 -> count = 4'b0000

        if (count === 4'b0000) begin
            $display("Time=%0t: Test Case %0d - boundary_test", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 4'b0000, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Time=%0t: Test Case %0d - boundary_test", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 4'b0000, count);
            failed_count = failed_count + 1;
        end

        // 测试4: long_run_test - 验证500个周期内计数是否连续正确
        test_number = test_number + 1;
        total_count = total_count + 1;

        reset = 1;
        #10;
        reset = 0;

        integer i;
        reg [3:0] expected;

        expected = 4'b0000;
        for (i = 0; i < 500; i = i + 1) begin
            #10; // 等待一个时钟周期
            expected = expected + 1;
            if (count !== expected) begin
                $display("Time=%0t: Test Case %0d - long_run_test (cycle %0d)", $time, test_number, i);
                $display("Expected: %h, Got: %h, Status: FAIL", expected, count);
                failed_count = failed_count + 1;
                break;
            end
        end

        if (i == 500) begin
            $display("Time=%0t: Test Case %0d - long_run_test", $time, test_number);
            $display("Expected: %h (after 500 cycles), Got: %h, Status: PASS", expected, count);
            passed_count = passed_count + 1;
        end

        // 输出统计信息
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
        $finish;
    end

endmodule