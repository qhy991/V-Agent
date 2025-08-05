`timescale 1ns/1ps

module tb_counter;
    // 信号声明
    reg clk;
    reg reset;
    reg enable;
    wire [3:0] count;

    // 实例化被测模块
    counter uut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .count(count)
    );

    // 时钟生成: 10ns周期 (5ns低, 5ns高)
    always #5 clk = ~clk;

    // 初始化测试
    initial begin
        // 打开波形转储（可选）
        $dumpfile("counter_wave.vcd");
        $dumpvars(0, tb_counter);

        // 初始化信号
        clk = 0;
        reset = 1;
        enable = 0;

        // 复位保持10个时钟周期
        repeat(10) @(posedge clk);
        reset = 0;

        // 启用计数器
        enable = 1;

        // 观察计数行为：运行20个时钟周期
        repeat(20) @(posedge clk);

        // 验证最终计数值
        if (count == 4'd20) begin
            $display("[PASS] Test passed: count = %d as expected.", count);
        end else begin
            $display("[FAIL] Test failed: expected count = 20, got %d", count);
        end

        // 结束仿真
        $finish;
    end
endmodule