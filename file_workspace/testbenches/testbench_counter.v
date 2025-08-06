`timescale 1ns / 1ps

module counter_tb;

    // 信号声明
    reg         clk;
    reg         reset;
    reg         enable;
    wire [7:0]  count;

    // 测试计数器
    integer     passed_count = 0;
    integer     failed_count = 0;
    integer     total_count = 0;
    integer     test_number;

    // 时钟周期定义 (10.0 ns)
    parameter CLK_PERIOD = 10.0;

    // 实例化被测模块
    counter uut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .count(count)
    );

    // 时钟生成 (50% duty cycle)
    always begin
        clk = 0;
        #(CLK_PERIOD / 2);
        clk = 1;
        #(CLK_PERIOD / 2);
    end

    // 初始化和测试激励
    initial begin
        // 打开VCD波形转储
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);

        // 初始化输入信号
        reset = 1;
        enable = 0;

        // 等待几个时钟周期以确保复位生效
        @(posedge clk);
        @(posedge clk);
        @(posedge clk);

        // 开始测试
        $display("Starting counter testbench...");

        // ========================
        // Test Case 1: reset_test
        // ========================
        test_number = 1;
        $display("Time=%0t: Test Case %0d - reset_test", $time, test_number);

        reset = 1;
        enable = 1;
        @(posedge clk);
        @(posedge clk);

        if (count == 8'd0) begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'd0, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'd0, count);
            failed_count = failed_count + 1;
        end
        total_count = total_count + 1;

        // ========================
        // Test Case 2: enable_test
        // ========================
        test_number = 2;
        $display("Time=%0t: Test Case %0d - enable_test", $time, test_number);

        reset = 0;
        enable = 0;
        @(posedge clk);
        @(posedge clk);
        @(posedge clk);

        if (count == 8'd0) begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'd0, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'd0, count);
            failed_count = failed_count + 1;
        end
        total_count = total_count + 1;

        // ========================
        // Test Case 3: counting_test
        // ========================
        test_number = 3;
        $display("Time=%0t: Test Case %0d - counting_test", $time, test_number);

        reset = 0;
        enable = 1;
        repeat(5) @(posedge clk);

        if (count == 8'd5) begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'd5, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'd5, count);
            failed_count = failed_count + 1;
        end
        total_count = total_count + 1;

        // ========================
        // Test Case 4: overflow_test
        // ========================
        test_number = 4;
        $display("Time=%0t: Test Case %0d - overflow_test", $time, test_number);

        // 手动设置计数器接近溢出
        // 由于无法直接写入reg，我们通过使能让其自然递增到255
        // 从当前值开始，需要 (255 - count) 个周期到达255
        integer i;
        integer target;
        target = 255 - count;

        for (i = 0; i < target; i = i + 1) begin
            @(posedge clk);
        end

        // 此时 count 应为 255
        if (count == 8'd255) begin
            $display("Count reached 255 as expected.");
        end else begin
            $display("FAIL: Expected count=255 before overflow, got %h", count);
            failed_count = failed_count + 1;
            total_count = total_count + 1;
            goto end_overflow_test;
        end

        // 下一个时钟上升沿应导致回滚到0
        @(posedge clk);

        if (count == 8'd0) begin
            $display("Expected: %h, Got: %h, Status: PASS", 8'd0, count);
            passed_count = passed_count + 1;
        end else begin
            $display("Expected: %h, Got: %h, Status: FAIL", 8'd0, count);
            failed_count = failed_count + 1;
        end
        total_count = total_count + 1;

        end_overflow_test:

        // ========================
        // Final Test Summary
        // ========================
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

    // 可选：监控信号变化
    initial begin
        $monitor("Time=%0t | clk=%b reset=%b enable=%b count=%h", 
                 $time, clk, reset, enable, count);
    end

endmodule