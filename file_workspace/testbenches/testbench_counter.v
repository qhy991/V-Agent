module testbench_counter;

    // 测试平台参数定义
    parameter CLK_PERIOD = 10.0; // 时钟周期(ns)
    parameter SIMULATION_TIME = 10000; // 仿真时间(ns)
    parameter ERROR_TOLERANCE = 0.01; // 允许的误差范围

    // 测试信号声明
    reg clk;
    reg rst_n;
    reg enable;
    wire [3:0] count;

    // 被测模块实例化
    counter uut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .count(count)
    );

    // 时钟生成
    always begin
        # (CLK_PERIOD / 2) clk = ~clk;
    end

    // 测试任务定义
    task automatic check_count(input [3:0] expected_count, input string test_name);
        real expected_time = $time;
        #1;
        if (count !== expected_count) begin
            $display("[ERROR] %s failed: Expected count = %d (0x%h), Got = %d (0x%h) at time %0t",
                      test_name, expected_count, expected_count, count, count, $time);
            $finish;
        end else begin
            $display("[INFO] %s passed: Count = %d (0x%h) at time %0t",
                      test_name, count, count, $time);
        end
    endtask

    // 测试初始化
    initial begin
        reg [3:0] expected;
        reg [3:0] actual;

        // 初始化测试信号
        clk = 0;
        rst_n = 0;
        enable = 0;
        
        // 测试开始信息
        $display("[INFO] Simulation started at time %0t", $time);
        
        // 基本测试场景
        $display("\n[INFO] Running basic test scenario");
        #100;
        rst_n = 1;
        enable = 1;
        check_count(0, "Initial count after reset");
        #100;
        @(posedge clk);
        check_count(1, "Count after 1 clock cycle");
        #100;
        @(posedge clk);
        check_count(2, "Count after 2 clock cycles");
        #100;
        @(posedge clk);
        check_count(3, "Count after 3 clock cycles");
        
        // 复位测试
        $display("\n[INFO] Running reset test scenario");
        #100;
        rst_n = 0;
        @(posedge clk);
        check_count(0, "Count after reset assertion");
        #100;
        rst_n = 1;
        @(posedge clk);
        check_count(0, "Count after reset release");
        #100;
        @(posedge clk);
        check_count(1, "Count after reset release and 1 cycle");
        
        // 使能测试
        $display("\n[INFO] Running enable test scenario");
        #100;
        enable = 0;
        @(posedge clk);
        check_count(2, "Count when enable is disabled");
        #100;
        @(posedge clk);
        check_count(2, "Count remains when enable is disabled");
        #100;
        enable = 1;
        @(posedge clk);
        check_count(3, "Count after enable re-enabled");
        #100;
        @(posedge clk);
        check_count(4, "Count increments after enable re-enabled");
        
        // 溢出测试
        $display("\n[INFO] Running rollover test scenario");
        $display("[INFO] Setting count to 15 (maximum value)");
        enable = 1;
        for (int i = 0; i < 12; i = i + 1) begin
            #100;
            @(posedge clk);
        end
        check_count(4'd15, "Count at maximum value");
        #100;
        @(posedge clk);
        check_count(4'd0, "Count after rollover");
        
        // 测试结束
        $display("\n[INFO] All tests completed successfully at time %0t", $time);
        $finish;
    end

    // 信号波形转储
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, testbench_counter);
    end

endmodule