`timescale 1ns / 1ps

module tb_adder_16bit;

    // 参数定义
    parameter CLK_PERIOD = 10.0; // 时钟周期 10.0ns

    // 信号声明
    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // 时钟和复位信号
    reg clk;
    reg rst_n;

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
    initial begin
        clk = 0;
        forever begin
            # (CLK_PERIOD / 2) clk = ~clk;
        end
    end

    // 复位生成
    initial begin
        rst_n = 0;
        # (CLK_PERIOD * 2);
        rst_n = 1;
    end

    // 波形转储设置
    initial begin
        $dumpfile("tb_adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
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
            $display("Test 1 Passed.");
        else
            $display("Test 1 Failed.");

        // 测试 0xFFFF + 0x0001 = 0x0000 (进位)
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000 && cout == 1'b1 && overflow == 1'b0)
            $display("Test 2 Passed.");
        else
            $display("Test 2 Failed.");

        // 测试 0x7FFF + 0x0001 = 0x8000 (溢出)
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h8000 && cout == 1'b0 && overflow == 1'b1)
            $display("Test 3 Passed.");
        else
            $display("Test 3 Failed.");
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
            $display("Carry Propagation Test 1 Passed.");
        else
            $display("Carry Propagation Test 1 Failed.");

        // 测试连续进位
        a = 16'h000F;
        b = 16'h0000;
        cin = 1'b1;
        #CLK_PERIOD;
        assert (sum == 16'h0010 && cout == 1'b0 && overflow == 1'b0)
            $display("Carry Propagation Test 2 Passed.");
        else
            $display("Carry Propagation Test 2 Failed.");
    endtask

    // 溢出检测测试
    task overflow_test;
        $display("=== Overflow Test ===");

        // 正数 + 正数 = 负数（溢出）
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h8000 && overflow == 1'b1)
            $display("Overflow Test 1 Passed.");
        else
            $display("Overflow Test 1 Failed.");

        // 负数 + 负数 = 正数（溢出）
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000 && overflow == 1'b1)
            $display("Overflow Test 2 Passed.");
        else
            $display("Overflow Test 2 Failed.");

        // 正数 + 正数 = 正数（无溢出）
        a = 16'h7FFE;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h7FFF && overflow == 1'b0)
            $display("Overflow Test 3 Passed.");
        else
            $display("Overflow Test 3 Failed.");
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
            $display("Boundary Test 1 Passed.");
        else
            $display("Boundary Test 1 Failed.");

        // 0xFFFF + 0xFFFF = 0xFFFE (进位)
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'hFFFE && cout == 1'b1 && overflow == 1'b0)
            $display("Boundary Test 2 Passed.");
        else
            $display("Boundary Test 2 Failed.");
    endtask

    // 随机数据测试
    task random_data_test;
        $display("=== Random Data Test ===");

        // 生成 100 个随机测试用例
        for (int i = 0; i < 100; i++) begin
            a = $random;
            b = $random;
            cin = $random % 2;
            #CLK_PERIOD;

            // 计算预期结果
            logic [16:0] expected_sum;
            expected_sum = a + b + cin;

            // 检查结果
            if (expected_sum[15] != sum) begin
                $display("Random Test %d Failed: Expected sum=0x%04h, Got=0x%04h", i, expected_sum[15:0], sum);
            end else begin
                $display("Random Test %d Passed.", i);
            end

            // 检查进位
            if (expected_sum[16] != cout) begin
                $display("Random Test %d Carry Failed: Expected cout=%b, Got=%b", i, expected_sum[16], cout);
            end

            // 检查溢出
            if ((a[15] == b[15]) && (a[15] != sum[15]) != overflow) begin
                $display("Random Test %d Overflow Failed: Expected overflow=%b, Got=%b", i, (a[15] == b[15]) && (a[15] != sum[15]), overflow);
            end
        end
    endtask

endmodule