`timescale 1ns / 1ps

module adder_16bit_tb;

    // 时钟周期定义
    parameter CLK_PERIOD = 10.0;

    // 信号声明
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
    reg clk;
    always # (CLK_PERIOD/2) clk = ~clk;

    // 复位生成（可选）
    reg rst_n;
    initial begin
        rst_n = 0;
        # (CLK_PERIOD * 2);
        rst_n = 1;
    end

    // 波形转储设置
    initial begin
        $dumpfile("adder_16bit_tb.vcd");
        $dumpvars(0, adder_16bit_tb);
    end

    // 测试报告输出
    initial begin
        $monitor("Time=%0t | a=0x%04h, b=0x%04h, cin=%b | sum=0x%04h, cout=%b, overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);
    end

    // 测试场景：基本加法运算
    task basic_test;
        input [15:0] a_val;
        input [15:0] b_val;
        input        cin_val;
        input [15:0] expected_sum;
        input        expected_cout;
        input        expected_overflow;

        begin
            a = a_val;
            b = b_val;
            cin = cin_val;
            #CLK_PERIOD;

            if (sum !== expected_sum) begin
                $display("ERROR: Basic test failed at %0t", $time);
                $display("  a=0x%04h, b=0x%04h, cin=%b", a_val, b_val, cin_val);
                $display("  Expected sum=0x%04h, got=0x%04h", expected_sum, sum);
            end

            if (cout !== expected_cout) begin
                $display("ERROR: Carry out mismatch in basic test at %0t", $time);
                $display("  Expected cout=%b, got=%b", expected_cout, cout);
            end

            if (overflow !== expected_overflow) begin
                $display("ERROR: Overflow mismatch in basic test at %0t", $time);
                $display("  Expected overflow=%b, got=%b", expected_overflow, overflow);
            end
        end
    endtask

    // 测试场景：进位传播测试
    task carry_propagation_test;
        input [15:0] a_val;
        input [15:0] b_val;
        input        cin_val;
        input [15:0] expected_sum;
        input        expected_cout;
        input        expected_overflow;

        begin
            a = a_val;
            b = b_val;
            cin = cin_val;
            #CLK_PERIOD;

            if (sum !== expected_sum) begin
                $display("ERROR: Carry propagation test failed at %0t", $time);
                $display("  a=0x%04h, b=0x%04h, cin=%b", a_val, b_val, cin_val);
                $display("  Expected sum=0x%04h, got=0x%04h", expected_sum, sum);
            end

            if (cout !== expected_cout) begin
                $display("ERROR: Carry out mismatch in carry propagation test at %0t", $time);
                $display("  Expected cout=%b, got=%b", expected_cout, cout);
            end

            if (overflow !== expected_overflow) begin
                $display("ERROR: Overflow mismatch in carry propagation test at %0t", $time);
                $display("  Expected overflow=%b, got=%b", expected_overflow, overflow);
            end
        end
    endtask

    // 测试场景：溢出检测测试
    task overflow_test;
        input [15:0] a_val;
        input [15:0] b_val;
        input        cin_val;
        input [15:0] expected_sum;
        input        expected_cout;
        input        expected_overflow;

        begin
            a = a_val;
            b = b_val;
            cin = cin_val;
            #CLK_PERIOD;

            if (sum !== expected_sum) begin
                $display("ERROR: Overflow test failed at %0t", $time);
                $display("  a=0x%04h, b=0x%04h, cin=%b", a_val, b_val, cin_val);
                $display("  Expected sum=0x%04h, got=0x%04h", expected_sum, sum);
            end

            if (cout !== expected_cout) begin
                $display("ERROR: Carry out mismatch in overflow test at %0t", $time);
                $display("  Expected cout=%b, got=%b", expected_cout, cout);
            end

            if (overflow !== expected_overflow) begin
                $display("ERROR: Overflow mismatch in overflow test at %0t", $time);
                $display("  Expected overflow=%b, got=%b", expected_overflow, overflow);
            end
        end
    endtask

    // 测试场景：边界值测试
    task boundary_value_test;
        input [15:0] a_val;
        input [15:0] b_val;
        input        cin_val;
        input [15:0] expected_sum;
        input        expected_cout;
        input        expected_overflow;

        begin
            a = a_val;
            b = b_val;
            cin = cin_val;
            #CLK_PERIOD;

            if (sum !== expected_sum) begin
                $display("ERROR: Boundary value test failed at %0t", $time);
                $display("  a=0x%04h, b=0x%04h, cin=%b", a_val, b_val, cin_val);
                $display("  Expected sum=0x%04h, got=0x%04h", expected_sum, sum);
            end

            if (cout !== expected_cout) begin
                $display("ERROR: Carry out mismatch in boundary value test at %0t", $time);
                $display("  Expected cout=%b, got=%b", expected_cout, cout);
            end

            if (overflow !== expected_overflow) begin
                $display("ERROR: Overflow mismatch in boundary value test at %0t", $time);
                $display("  Expected overflow=%b, got=%b", expected_overflow, overflow);
            end
        end
    endtask

    // 测试场景：随机数据测试
    task random_data_test;
        input [15:0] a_val;
        input [15:0] b_val;
        input        cin_val;
        input [15:0] expected_sum;
        input        expected_cout;
        input        expected_overflow;

        begin
            a = a_val;
            b = b_val;
            cin = cin_val;
            #CLK_PERIOD;

            if (sum !== expected_sum) begin
                $display("ERROR: Random data test failed at %0t", $time);
                $display("  a=0x%04h, b=0x%04h, cin=%b", a_val, b_val, cin_val);
                $display("  Expected sum=0x%04h, got=0x%04h", expected_sum, sum);
            end

            if (cout !== expected_cout) begin
                $display("ERROR: Carry out mismatch in random data test at %0t", $time);
                $display("  Expected cout=%b, got=%b", expected_cout, cout);
            end

            if (overflow !== expected_overflow) begin
                $display("ERROR: Overflow mismatch in random data test at %0t", $time);
                $display("  Expected overflow=%b, got=%b", expected_overflow, overflow);
            end
        end
    endtask

    // 主测试流程
    initial begin
        // 初始化
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #CLK_PERIOD;

        // 基本加法测试
        basic_test(16'h0001, 16'h0002, 1'b0, 16'h0003, 1'b0, 1'b0);
        basic_test(16'h000F, 16'h0001, 1'b0, 16'h0010, 1'b0, 1'b0);
        basic_test(16'hFFFF, 16'h0001, 1'b0, 16'h0000, 1'b1, 1'b0);

        // 进位传播测试
        carry_propagation_test(16'h0000, 16'h0000, 1'b1, 16'h0001, 1'b0, 1'b0);
        carry_propagation_test(16'h0000, 16'h0000, 1'b1, 16'h0001, 1'b0, 1'b0);
        carry_propagation_test(16'h00FF, 16'h0000, 1'b1, 16'h0100, 1'b0, 1'b0);
        carry_propagation_test(16'hFFFF, 16'h0000, 1'b1, 16'h0000, 1'b1, 1'b0);

        // 溢出检测测试
        overflow_test(16'h7FFF, 16'h0001, 1'b0, 16'h8000, 1'b0, 1'b1);
        overflow_test(16'h8000, 16'h8000, 1'b0, 16'h0000, 1'b1, 1'b1);
        overflow_test(16'h7FFF, 16'h7FFF, 1'b0, 16'hFFFF, 1'b0, 1'b1);
        overflow_test(16'h8000, 16'h8000, 1'b0, 16'h0000, 1'b1, 1'b1);

        // 边界值测试
        boundary_value_test(16'h0000, 16'h0000, 1'b0, 16'h0000, 1'b0, 1'b0);
        boundary_value_test(16'hFFFF, 16'hFFFF, 1'b0, 16'hFFFE, 1'b1, 1'b0);
        boundary_value_test(16'h7FFF, 16'h7FFF, 1'b0, 16'hFFFF, 1'b0, 1'b1);
        boundary_value_test(16'h8000, 16'h8000, 1'b0, 16'h0000, 1'b1, 1'b1);

        // 随机数据测试（使用随机数生成器）
        integer i;
        for (i = 0; i < 100; i = i + 1) begin
            a = $random();
            b = $random();
            cin = $random() % 2;
            #CLK_PERIOD;

            // 计算预期结果（手动计算或通过C语言模拟）
            // 这里假设我们有预计算的期望值
            // 可以替换为实际计算逻辑
            // 例如：
            // expected_sum = a + b + cin;
            // expected_cout = (a + b + cin) > 16'hFFFF ? 1 : 0;
            // expected_overflow = ((a[15] == b[15]) && (a[15] != sum[15]));

            // 调用随机数据测试任务
            random_data_test(a, b, cin, expected_sum, expected_cout, expected_overflow);
        end

        // 结束仿真
        # (CLK_PERIOD * 10);
        $display("All tests completed.");
        $finish;
    end

endmodule