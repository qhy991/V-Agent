`timescale 1ns / 1ps

module tb_adder_16bit;

    // 时钟周期定义
    parameter CLK_PERIOD = 10.0;

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

    // 被测模块实例化
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // 波形转储设置
    initial begin
        $dumpfile("tb_adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // 时钟生成逻辑
    always # (CLK_PERIOD/2) clk = ~clk;

    // 复位生成逻辑
    initial begin
        clk = 0;
        rst_n = 0;
        # (CLK_PERIOD * 2); // 等待两个时钟周期
        rst_n = 1;
    end

    // 测试场景控制
    reg [3:0] test_case;

    // 测试报告输出
    initial begin
        $monitor("Time: %t | a=0x%04h, b=0x%04h, cin=%b, sum=0x%04h, cout=%b, overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);

        // 初始化输入
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;

        // 设置测试用例
        test_case = 0;

        // 执行所有测试场景
        # (CLK_PERIOD * 2); // 等待复位完成

        // 基本加法测试
        basic_addition();

        // 进位传播测试
        carry_propagation();

        // 溢出检测测试
        overflow_detection();

        // 边界值测试
        boundary_values();

        // 随机数据测试
        random_data();

        // 结束仿真
        # (CLK_PERIOD * 10);
        $finish;
    end

    // 基本加法测试
    task basic_addition;
        $display("=== Running Basic Addition Test ===");

        // 测试 1 + 1 = 2
        a = 16'h0001;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0002 && cout == 1'b0 && overflow == 1'b0)
            $display("PASS: Basic addition 1+1=2");
        else
            $display("FAIL: Basic addition 1+1=2");

        // 测试 0xFFFF + 0x0001 = 0x0000 (溢出)
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0000 && cout == 1'b1 && overflow == 1'b1)
            $display("PASS: Overflow case 0xFFFF + 0x0001 = 0x0000");
        else
            $display("FAIL: Overflow case 0xFFFF + 0x0001 = 0x0000");

        // 测试 0x8000 + 0x8000 = 0x0000 (溢出)
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0000 && cout == 1'b1 && overflow == 1'b1)
            $display("PASS: Overflow case 0x8000 + 0x8000 = 0x0000");
        else
            $display("FAIL: Overflow case 0x8000 + 0x8000 = 0x0000");

        // 测试 0x7FFF + 0x0001 = 0x8000 (溢出)
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h8000 && cout == 1'b0 && overflow == 1'b1)
            $display("PASS: Overflow case 0x7FFF + 0x0001 = 0x8000");
        else
            $display("FAIL: Overflow case 0x7FFF + 0x0001 = 0x8000");

        // 测试 0x0000 + 0x0000 = 0x0000
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0000 && cout == 1'b0 && overflow == 1'b0)
            $display("PASS: Zero addition");
        else
            $display("FAIL: Zero addition");
    endtask

    // 进位传播测试
    task carry_propagation;
        $display("=== Running Carry Propagation Test ===");

        // 测试进位从低位到高位的传播
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b1;
        #CLK_PERIOD;

        assert (sum == 16'h0001 && cout == 1'b0 && overflow == 1'b0)
            $display("PASS: Carry propagation from LSB");
        else
            $display("FAIL: Carry propagation from LSB");

        // 测试进位从高位到低位的传播
        a = 16'hFFFF;
        b = 16'hFFFF;
        cin = 1'b1;
        #CLK_PERIOD;

        assert (sum == 16'hFFFE && cout == 1'b1 && overflow == 1'b1)
            $display("PASS: Carry propagation from MSB");
        else
            $display("FAIL: Carry propagation from MSB");
    endtask

    // 溢出检测测试
    task overflow_detection;
        $display("=== Running Overflow Detection Test ===");

        // 正数 + 正数 = 负数 → 溢出
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h8000 && overflow == 1'b1)
            $display("PASS: Overflow detection for positive + positive");
        else
            $display("FAIL: Overflow detection for positive + positive");

        // 负数 + 负数 = 正数 → 溢出
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0000 && overflow == 1'b1)
            $display("PASS: Overflow detection for negative + negative");
        else
            $display("FAIL: Overflow detection for negative + negative");

        // 正数 + 正数 = 正数 → 不溢出
        a = 16'h7FFE;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h7FFF && overflow == 1'b0)
            $display("PASS: No overflow for positive + positive");
        else
            $display("FAIL: No overflow for positive + positive");

        // 负数 + 负数 = 负数 → 不溢出
        a = 16'h8001;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0001 && overflow == 1'b0)
            $display("PASS: No overflow for negative + negative");
        else
            $display("FAIL: No overflow for negative + negative");
    endtask

    // 边界值测试
    task boundary_values;
        $display("=== Running Boundary Values Test ===");

        // 0x0000 + 0x0000 = 0x0000
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0000 && overflow == 1'b0)
            $display("PASS: 0x0000 + 0x0000");
        else
            $display("FAIL: 0x0000 + 0x0000");

        // 0xFFFF + 0x0000 = 0xFFFF
        a = 16'hFFFF;
        b = 16'h0000;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'hFFFF && overflow == 1'b0)
            $display("PASS: 0xFFFF + 0x0000");
        else
            $display("FAIL: 0xFFFF + 0x0000");

        // 0xFFFF + 0x0001 = 0x0000 (溢出)
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0000 && overflow == 1'b1)
            $display("PASS: 0xFFFF + 0x0001");
        else
            $display("FAIL: 0xFFFF + 0x0001");

        // 0x8000 + 0x8000 = 0x0000 (溢出)
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;

        assert (sum == 16'h0000 && overflow == 1'b1)
            $display("PASS: 0x8000 + 0x8000");
        else
            $display("FAIL: 0x8000 + 0x8000");
    endtask

    // 随机数据测试
    task random_data;
        $display("=== Running Random Data Test ===");

        // 生成随机数据并进行测试
        for (int i = 0; i < 100; i++) begin
            a = $random();
            b = $random();
            cin = $random() % 2;
            #CLK_PERIOD;

            // 检查结果是否符合预期
            if ($signed(a) + $signed(b) + $signed(cin) > 16'h7FFF) begin
                // 溢出情况
                assert (sum == $unsigned(a + b + cin) && overflow == 1'b1)
                    $display("PASS: Random data with overflow");
                else
                    $display("FAIL: Random data with overflow");
            end else if ($signed(a) + $signed(b) + $signed(cin) < -16'h8000) begin
                // 下溢情况
                assert (sum == $unsigned(a + b + cin) && overflow == 1'b1)
                    $display("PASS: Random data with underflow");
                else
                    $display("FAIL: Random data with underflow");
            end else begin
                assert (sum == $unsigned(a + b + cin) && overflow == 1'b0)
                    $display("PASS: Random data without overflow");
                else
                    $display("FAIL: Random data without overflow");
            end
        end
    endtask

endmodule