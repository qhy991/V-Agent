`timescale 1ns / 1ps

module counter_tb;

    // 定义时钟周期
    parameter CLK_PERIOD = 10.0;

    // 声明信号
    reg clk;
    reg rst;
    wire [3:0] count;

    // 被测模块实例化
    counter uut (
        .clk(clk),
        .rst(rst),
        .count(count)
    );

    // 测试计数器变量
    integer passed_count = 0;
    integer failed_count = 0;
    integer total_count = 0;

    // 测试用例编号和名称
    integer test_number = 0;
    string test_name;

    // 时钟生成
    always begin
        # (CLK_PERIOD / 2) clk = ~clk;
    end

    // 波形转储
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);
    end

    // 初始化
    initial begin
        clk = 0;
        rst = 1;

        // 等待复位释放
        # (CLK_PERIOD * 2);
        rst = 0;

        // 执行测试用例
        test_number = test_number + 1;
        test_name = "basic_count_test";
        total_count = total_count + 1;
        basic_count_test();
        # (CLK_PERIOD * 10);

        test_number = test_number + 1;
        test_name = "reset_test";
        total_count = total_count + 1;
        reset_test();
        # (CLK_PERIOD * 10);

        test_number = test_number + 1;
        test_name = "rollover_test";
        total_count = total_count + 1;
        rollover_test();
        # (CLK_PERIOD * 10);

        // 输出测试统计
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

    // 测试用例：基本计数功能
    task basic_count_test;
        integer i;
        reg [3:0] expected;
        expected = 4'd0;

        $display("Time=%0t: Test Case %0d - %s", $time, test_number, test_name);

        for (i = 0; i < 10; i = i + 1) begin
            @(posedge clk);
            expected = expected + 1;
            if (count === expected) begin
                $display("Expected: %h, Got: %h, Status: PASS", expected, count);
                passed_count = passed_count + 1;
            end else begin
                $display("Expected: %h, Got: %h, Status: FAIL", expected, count);
                failed_count = failed_count + 1;
            end
        end
    endtask

    // 测试用例：复位功能
    task reset_test;
        integer i;

        $display("Time=%0t: Test Case %0d - %s", $time, test_number, test_name);

        // 触发复位
        rst = 1;
        @(posedge clk);
        rst = 0;

        if (count === 4'd0) begin
            $display("Expected: %h, Got: %h, Status: PASS", 4'd0, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 4'd0, count);
            failed_count = failed_count + 1;
        end

        // 检查复位后是否继续计数
        for (i = 0; i < 5; i = i + 1) begin
            @(posedge clk);
        end

        if (count === 4'd5) begin
            $display("Expected: %h, Got: %h, Status: PASS", 4'd5, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 4'd5, count);
            failed_count = failed_count + 1;
        end
    endtask

    // 测试用例：溢出功能
    task rollover_test;
        integer i;
        reg [3:0] expected;

        $display("Time=%0t: Test Case %0d - %s", $time, test_number, test_name);

        // 手动设置计数器接近最大值
        force uut.count = 4'd14;
        @(posedge clk);
        release uut.count;

        expected = 4'd15;
        @(posedge clk);
        if (count === expected) begin
            $display("Expected: %h, Got: %h, Status: PASS", expected, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", expected, count);
            failed_count = failed_count + 1;
        end

        expected = 4'd0;
        @(posedge clk);
        if (count === expected) begin
            $display("Expected: %h, Got: %h, Status: PASS", expected, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", expected, count);
            failed_count = failed_count + 1;
        end
    endtask

endmodule