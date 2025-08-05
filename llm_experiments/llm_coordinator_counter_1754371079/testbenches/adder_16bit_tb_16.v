`timescale 1ns / 1ps

module tb_adder_16bit;

    // 时钟周期定义
    parameter CLK_PERIOD = 10.0ns;

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

    // 波形转储设置
    initial begin
        $dumpfile("tb_adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // 被测模块实例化
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // 时钟生成逻辑
    always # (CLK_PERIOD/2) clk = ~clk;

    // 复位生成逻辑
    initial begin
        clk = 0;
        rst_n = 0;
        # (CLK_PERIOD * 2);
        rst_n = 1;
    end

    // 测试场景控制
    reg [3:0] test_case;
    localparam IDLE = 4'b0000,
               BASIC_ADDITION = 4'b0001,
               CARRY_PROPAGATION = 4'b0010,
               OVERFLOW_DETECTION = 4'b0011,
               BOUNDARY_VALUES = 4'b0100,
               RANDOM_DATA = 4'b0101;

    // 测试报告变量
    integer test_passed;
    integer test_failed;

    // 初始化测试计数器
    initial begin
        test_passed = 0;
        test_failed = 0;
    end

    // 主测试流程
    initial begin
        // 初始状态
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;

        // 等待复位完成
        # (CLK_PERIOD * 2);

        // 开始测试
        test_case = BASIC_ADDITION;
        $display("=== Starting Basic Addition Test ===");
        basic_addition();
        $display("Basic Addition Test %s", (test_passed > 0 && test_failed == 0) ? "PASSED" : "FAILED");

        test_case = CARRY_PROPAGATION;
        $display("=== Starting Carry Propagation Test ===");
        carry_propagation();
        $display("Carry Propagation Test %s", (test_passed > 0 && test_failed == 0) ? "PASSED" : "FAILED");

        test_case = OVERFLOW_DETECTION;
        $display("=== Starting Overflow Detection Test ===");
        overflow_detection();
        $display("Overflow Detection Test %s", (test_passed > 0 && test_failed == 0) ? "PASSED" : "FAILED");

        test_case = BOUNDARY_VALUES;
        $display("=== Starting Boundary Values Test ===");
        boundary_values();
        $display("Boundary Values Test %s", (test_passed > 0 && test_failed == 0) ? "PASSED" : "FAILED");

        test_case = RANDOM_DATA;
        $display("=== Starting Random Data Test ===");
        random_data();
        $display("Random Data Test %s", (test_passed > 0 && test_failed == 0) ? "PASSED" : "FAILED");

        // 显示最终测试结果
        $display("=== Final Test Results ===");
        $display("Tests Passed: %d", test_passed);
        $display("Tests Failed: %d", test_failed);
        $display("Total Tests: %d", test_passed + test_failed);
        
        if (test_failed == 0) begin
            $display("🎉 All tests PASSED!");
        end else begin
            $display("❌ Some tests FAILED!");
        end
        
        // 结束仿真
        #(CLK_PERIOD * 10);
        $display("Simulation completed.");
        $finish;

        // 显示最终测试结果
        $display("=== Final Test Report ===");
        $display("Total Passed Tests: %d", test_passed);
        $display("Total Failed Tests: %d", test_failed);
        $display("Test Coverage: %.2f%%", (test_passed / (test_passed + test_failed)) * 100);
        $finish;
    end

    // 基本加法测试
    task basic_addition;
        // 测试用例：a + b = sum
        // 验证基本加法功能
        $display("Running Basic Addition Test...");

        // 测试用例 1: 0x0000 + 0x0000 = 0x0000
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Basic Addition Test 1 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 测试用例 2: 0x0001 + 0x0002 = 0x0003
        a = 16'h0001;
        b = 16'h0002;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0003) else begin
            $display("Error: Basic Addition Test 2 failed. Expected 0x0003, got %h", sum);
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 测试用例 3: 0x7FFF + 0x0001 = 0x8000 (溢出)
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h8000) else begin
            $display("Error: Basic Addition Test 3 failed. Expected 0x8000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (overflow == 1'b1) else begin
            $display("Error: Overflow not detected in Test 3.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 测试用例 4: 0x8000 + 0x8000 = 0x0000 (溢出)
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Basic Addition Test 4 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (overflow == 1'b1) else begin
            $display("Error: Overflow not detected in Test 4.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 测试用例 5: 0xFFFF + 0x0001 = 0x0000 (进位)
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Basic Addition Test 5 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (cout == 1'b1) else begin
            $display("Error: Carry not generated in Test 5.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;
    endtask

    // 进位传播测试
    task carry_propagation;
        $display("Running Carry Propagation Test...");

        // 测试用例：连续进位
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b1;
        #CLK_PERIOD;
        assert (sum == 16'h0001) else begin
            $display("Error: Carry Propagation Test 1 failed. Expected 0x0001, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (cout == 1'b0) else begin
            $display("Error: Carry not cleared in Test 1.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        a = 16'h0001;
        b = 16'h0001;
        cin = 1'b1;
        #CLK_PERIOD;
        assert (sum == 16'h0003) else begin
            $display("Error: Carry Propagation Test 2 failed. Expected 0x0003, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (cout == 1'b0) else begin
            $display("Error: Carry not cleared in Test 2.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        a = 16'hFFFF;
        b = 16'h0000;
        cin = 1'b1;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Carry Propagation Test 3 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (cout == 1'b1) else begin
            $display("Error: Carry not generated in Test 3.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;
    endtask

    // 溢出检测测试
    task overflow_detection;
        $display("Running Overflow Detection Test...");

        // 正数 + 正数 = 负数 → 溢出
        a = 16'h7FFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h8000) else begin
            $display("Error: Overflow Detection Test 1 failed. Expected 0x8000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (overflow == 1'b1) else begin
            $display("Error: Overflow not detected in Test 1.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 负数 + 负数 = 正数 → 溢出
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Overflow Detection Test 2 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (overflow == 1'b1) else begin
            $display("Error: Overflow not detected in Test 2.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 正数 + 正数 = 正数 → 不溢出
        a = 16'h7FFE;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h7FFF) else begin
            $display("Error: Overflow Detection Test 3 failed. Expected 0x7FFF, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (overflow == 1'b0) else begin
            $display("Error: Overflow detected in Test 3 when it shouldn't be.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 负数 + 负数 = 负数 → 不溢出
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Overflow Detection Test 4 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (overflow == 1'b1) else begin
            $display("Error: Overflow not detected in Test 4.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;
    endtask

    // 边界值测试
    task boundary_values;
        $display("Running Boundary Values Test...");

        // 0x0000 + 0x0000 = 0x0000
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Boundary Values Test 1 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 0xFFFF + 0x0000 = 0xFFFF
        a = 16'hFFFF;
        b = 16'h0000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'hFFFF) else begin
            $display("Error: Boundary Values Test 2 failed. Expected 0xFFFF, got %h", sum);
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 0xFFFF + 0x0001 = 0x0000 (进位)
        a = 16'hFFFF;
        b = 16'h0001;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Boundary Values Test 3 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (cout == 1'b1) else begin
            $display("Error: Carry not generated in Test 3.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;

        // 0x8000 + 0x8000 = 0x0000 (溢出)
        a = 16'h8000;
        b = 16'h8000;
        cin = 1'b0;
        #CLK_PERIOD;
        assert (sum == 16'h0000) else begin
            $display("Error: Boundary Values Test 4 failed. Expected 0x0000, got %h", sum);
            test_failed = test_failed + 1;
        end;
        assert (overflow == 1'b1) else begin
            $display("Error: Overflow not detected in Test 4.");
            test_failed = test_failed + 1;
        end;
        test_passed = test_passed + 1;
    endtask

    // 随机数据测试
    task random_data;
        $display("Running Random Data Test...");

        // 生成随机数据并验证
        integer i;
        for (i = 0; i < 100; i = i + 1) begin
            a = $random;
            b = $random;
            cin = $random % 2;
            #CLK_PERIOD;

            // 验证结果
            if (a + b + cin != sum) begin
                $display("Error: Random Data Test %d failed. Expected %h, got %h", i, a + b + cin, sum);
                test_failed = test_failed + 1;
            end else begin
                test_passed = test_passed + 1;
            end
        end
    endtask

    // 实时监控输出
    initial begin
        $monitor("Time=%t, a=0x%04h, b=0x%04h, cin=%b, sum=0x%04h, cout=%b, overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);
    end

endmodule