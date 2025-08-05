`timescale 1ns / 1ps

module counter_tb;

    // 信号声明
    reg clk;
    reg rst;
    reg enable;
    wire [3:0] count;

    // 测试计数器变量
    integer passed_count = 0;
    integer failed_count = 0;
    integer total_count = 0;
    integer test_number = 0;
    reg [3:0] expected_count;

    // 被测模块实例化
    counter uut (
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .count(count)
    );

    // 时钟生成（周期10.0ns）
    always begin
        #5 clk = ~clk;
    end

    // 初始过程
    initial begin
        // 初始化信号
        clk = 0;
        rst = 0;
        enable = 0;

        // 打开波形转储
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);

        // 执行测试用例
        basic_test();
        reset_test();
        enable_test();
        overflow_test();

        // 打印统计信息
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

    // 基本功能测试
    task basic_test;
        integer i;
        begin
            test_number = test_number + 1;
            total_count = total_count + 1;

            rst = 1;
            enable = 0;
            #10 rst = 0;
            enable = 1;

            expected_count = 4'h0;
            for (i = 0; i < 5; i = i + 1) begin
                @(posedge clk);
                expected_count = expected_count + 1;
            end

            if (count === expected_count) begin
                $display("Time=%0t: Test Case %0d - basic_test", $time, test_number);
                $display("Expected: %h, Got: %h, Status: PASS", expected_count, count);
                passed_count = passed_count + 1;
            end else begin
                $display("Time=%0t: Test Case %0d - basic_test", $time, test_number);
                $display("Expected: %h, Got: %h, Status: FAIL", expected_count, count);
                failed_count = failed_count + 1;
            end
        end
    endtask

    // 复位功能测试
    task reset_test;
        integer i;
        begin
            test_number = test_number + 1;
            total_count = total_count + 1;

            rst = 1;
            enable = 0;
            #10 rst = 0;
            enable = 1;

            for (i = 0; i < 5; i = i + 1) begin
                @(posedge clk);
            end

            rst = 1;
            #10 rst = 0;

            expected_count = 4'h0;
            if (count === expected_count) begin
                $display("Time=%0t: Test Case %0d - reset_test", $time, test_number);
                $display("Expected: %h, Got: %h, Status: PASS", expected_count, count);
                passed_count = passed_count + 1;
            end else begin
                $display("Time=%0t: Test Case %0d - reset_test", $time, test_number);
                $display("Expected: %h, Got: %h, Status: FAIL", expected_count, count);
                failed_count = failed_count + 1;
            end
        end
    endtask

    // 使能控制测试
    task enable_test;
        integer i;
        begin
            test_number = test_number + 1;
            total_count = total_count + 1;

            rst = 1;
            enable = 0;
            #10 rst = 0;

            expected_count = count;

            for (i = 0; i < 5; i = i + 1) begin
                @(posedge clk);
            end

            if (count === expected_count) begin
                $display("Time=%0t: Test Case %0d - enable_test", $time, test_number);
                $display("Expected: %h, Got: %h, Status: PASS", expected_count, count);
                passed_count = passed_count + 1;
            end else begin
                $display("Time=%0t: Test Case %0d - enable_test", $time, test_number);
                $display("Expected: %h, Got: %h, Status: FAIL", expected_count, count);
                failed_count = failed_count + 1;
            end
        end
    endtask

    // 溢出边界测试
    task overflow_test;
        integer i;
        begin
            test_number = test_number + 1;
            total_count = total_count + 1;

            rst = 1;
            enable = 0;
            #10 rst = 0;
            enable = 1;

            expected_count = 4'hF; // 15
            for (i = 0; i < 15; i = i + 1) begin
                @(posedge clk);
            end

            if (count === expected_count) begin
                $display("Time=%0t: Test Case %0d - overflow_test", $time, test_number);
                $display("Expected: %h, Got: %h, Status: PASS", expected_count, count);
                passed_count = passed_count + 1;
            end else begin
                $display("Time=%0t: Test Case %0d - overflow_test", $time, test_number);
                $display("Expected: %h, Got: %h, Status: FAIL", expected_count, count);
                failed_count = failed_count + 1;
            end

            // 下一个周期应溢出为0
            expected_count = 4'h0;
            @(posedge clk);
            if (count === expected_count) begin
                $display("Time=%0t: Test Case %0d - overflow_test (overflow check)", $time, test_number);
                $display("Expected: %h, Got: %h, Status: PASS", expected_count, count);
                passed_count = passed_count + 1;
                total_count = total_count + 1;
            end else begin
                $display("Time=%0t: Test Case %0d - overflow_test (overflow check)", $time, test_number);
                $display("Expected: %h, Got: %h, Status: FAIL", expected_count, count);
                failed_count = failed_count + 1;
                total_count = total_count + 1;
            end
        end
    endtask

endmodule