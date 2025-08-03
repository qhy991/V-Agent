`timescale 1ns / 1ps

module adder_16bit_tb;

    // 时钟周期定义
    parameter CLK_PERIOD = 10.0ns;

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

    // 复位生成
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
        $monitor("Time: %t | a=0x%04h, b=0x%04h, cin=%b, sum=0x%04h, cout=%b, overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);

        // 基本加法测试
        basic_test();

        // 进位传播测试
        carry_propagation_test();

        // 溢出检测测试
        overflow_test();

        // 边界值测试
        boundary_value_test();

        // 随机数据测试
        random_data_test();

        // 结束仿真
        # (CLK_PERIOD * 10);
        $finish;
    end

    // 基本加法测试
    task basic_test;
        $display("=== Basic Test ===");

        // 测试 1 + 1 = 2
        a = 16'h0001;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0002 && cout == 1'b0 && overflow == 1'b0)
            $display("PASS: Basic test 1+1=2");
        else
            $display("FAIL: Basic test 1+1=2");

        // 测试 0xFFFF + 0x0001 = 0x0000 (溢出)
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000 && cout == 1'b1 && overflow == 1'b1)
            $display("PASS: Basic test 0xFFFF + 0x0001 = 0x0000 (overflow)");
        else
            $display("FAIL: Basic test 0xFFFF + 0x0001 = 0x0000 (overflow)");

        // 测试 0x8000 + 0x8000 = 0x0000 (溢出)
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000 && cout == 1'b1 && overflow == 1'b1)
            $display("PASS: Basic test 0x8000 + 0x8000 = 0x0000 (overflow)");
        else
            $display("FAIL: Basic test 0x8000 + 0x8000 = 0x0000 (overflow)");
    endtask

    // 进位传播测试
    task carry_propagation_test;
        $display("=== Carry Propagation Test ===");

        // 测试进位从低位到高位的传播
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b1;
        #CLK_PERIOD;
        assert (sum == 16'h0001 && cout == 1'b0 && overflow == 1'b0)
            $display("PASS: Carry propagation test 0+0+1=1");
        else
            $display("FAIL: Carry propagation test 0+0+1=1");

        // 测试连续进位
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b1;
        #CLK_PERIOD;
        assert (sum == 16'h0001 && cout == 1'b0 && overflow == 1'b0)
            $display("PASS: Carry propagation test 0+0+1=1 (again)");
        else
            $display("FAIL: Carry propagation test 0+0+1=1 (again)");
    endtask

    // 溢出检测测试
    task overflow_test;
        $display("=== Overflow Test ===");

        // 正数 + 正数 = 负数 → 溢出
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h8000 && cout == 1'b0 && overflow == 1'b1)
            $display("PASS: Overflow test 0x7FFF + 0x0001 = 0x8000 (overflow)");
        else
            $display("FAIL: Overflow test 0x7FFF + 0x0001 = 0x8000 (overflow)");

        // 负数 + 负数 = 正数 → 溢出
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000 && cout == 1'b1 && overflow == 1'b1)
            $display("PASS: Overflow test 0x8000 + 0x8000 = 0x0000 (overflow)");
        else
            $display("FAIL: Overflow test 0x8000 + 0x8000 = 0x0000 (overflow)");
    endtask

    // 边界值测试
    task boundary_value_test;
        $display("=== Boundary Value Test ===");

        // 0x0000 + 0x0000 = 0x0000
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000 && cout == 1'b0 && overflow == 1'b0)
            $display("PASS: Boundary test 0x0000 + 0x0000 = 0x0000");
        else
            $display("FAIL: Boundary test 0x0000 + 0x0000 = 0x0000");

        // 0xFFFF + 0xFFFF = 0xFFFE (进位)
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'hFFFE && cout == 1'b1 && overflow == 1'b0)
            $display("PASS: Boundary test 0xFFFF + 0xFFFF = 0xFFFE");
        else
            $display("FAIL: Boundary test 0xFFFF + 0xFFFF = 0xFFFE");

        // 0x8000 + 0x7FFF = 0xFFFF (溢出)
        a = 16'h8000;
        b = 16'h7FFF;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'hFFFF && cout == 1'b0 && overflow == 1'b1)
            $display("PASS: Boundary test 0x8000 + 0x7FFF = 0xFFFF (overflow)");
        else
            $display("FAIL: Boundary test 0x8000 + 0x7FFF = 0xFFFF (overflow)");
    endtask

    // 随机数据测试
    task random_data_test;
        $display("=== Random Data Test ===");

        // 生成随机输入并验证结果
        for (int i = 0; i < 100; i++) begin
            a = $random;
            b = $random;
            cin = $random % 2;
            #CLK_PERIOD;

            // 简单验证：检查是否与预期一致（使用C语言计算）
            // 注意：此处仅用于演示，实际应使用更精确的验证方法
            int expected_sum = (a + b + cin) & 16'hFFFF;
            int expected_cout = (a + b + cin) >> 16;
            int expected_overflow = ((a[15] == b[15]) && (a[15] != sum[15]));

            assert (sum == expected_sum && cout == expected_cout && overflow == expected_overflow)
                $display("PASS: Random test %d", i);
            else
                $display("FAIL: Random test %d", i);
        end
    endtask

endmodule