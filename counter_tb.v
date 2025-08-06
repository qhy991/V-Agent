`timescale 1ns / 1ps

module counter_tb;

    // 信号声明
    reg         clk;
    reg         rst;
    wire [31:0] count;

    // 测试计数器
    integer passed_count = 0;
    integer failed_count = 0;
    integer total_count = 0;

    // 实例化被测模块
    counter uut (
        .clk(clk),
        .rst(rst),
        .count(count)
    );

    // 生成时钟（周期10ns）
    parameter CLOCK_PERIOD = 10;
    always begin
        clk = 0;
        #(CLOCK_PERIOD/2);
        clk = 1;
        #(CLOCK_PERIOD/2);
    end

    // 初始化和测试激励
    initial begin
        $timeformat(-9, 2, "ns", 10);
        $display("==================================");
        $display("        Counter Module Test");
        $display("==================================");

        // 初始化输入
        rst = 1;
        @(posedge clk);
        rst = 0;

        $display("\n[Test: Basic Counting] - 验证前10个周期递增");
        repeat(10) begin
            @(posedge clk);
            if (count !== (count - 1 + 1)) begin  // 简化为 count == previous + 1 的等效检查
                $error("计数器未正确递增！期望值：%0d, 实际值：%0d", count-1+1, count);
                failed_count = failed_count + 1;
            end else begin
                $display("PASS: Time = %t | count = %0d", $time, count);
                passed_count = passed_count + 1;
            end
            total_count = total_count + 1;
        end

        $display("\n[Test: Synchronous Reset] - 在非零状态施加复位");
        rst = 1;
        @(posedge clk);
        if (count !== 0) begin
            $error("复位后 count 未归零！实际值：%0d", count);
            failed_count = failed_count + 1;
        end else begin
            $display("PASS: 复位成功：count == 0");
            passed_count = passed_count + 1;
        end
        rst = 0;
        total_count = total_count + 1;

        $display("\n[Test: Overflow Wraparound] - 验证32位溢出回绕");
        force uut.count = 32'hFFFFFFFE;
        @(posedge clk);
        if (count !== 32'hFFFFFFFE) begin
            $error("force失败：期望32'hFFFFFFFE，实际%0h", count);
            failed_count = failed_count + 1;
        end

        @(posedge clk);
        if (count !== 32'hFFFFFFFF) begin
            $error("未达到0xFFFFFFFF，实际%0h", count);
            failed_count = failed_count + 1;
        end

        @(posedge clk);
        if (count !== 0) begin
            $error("溢出后未回绕至0！当前值：%0d", count);
            failed_count = failed_count + 1;
        end else begin
            $display("PASS: 溢出回绕成功：32'hFFFFFFFF + 1 → 0");
            passed_count = passed_count + 1;
        end
        total_count = total_count + 1;

        release uut.count;

        $display("\n==================================");
        $display("          测试完成");
        $display("==================================");
        $display("总计: %0d / %0d 测试通过", passed_count, total_count);
        if (failed_count == 0) $display("** All tests passed! **");
        else $display("** %0d tests failed **", failed_count);
        $finish;
    end

    // 生成VCD波形
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);
    end

endmodule