module testbench_counter;
    reg clk;
    reg rst;
    reg enable;
    wire [3:0] count;

    // 实例化被测模块
    counter uut (
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .count(count)
    );

    // 生成时钟信号
    parameter CLOCK_PERIOD = 10;
    initial begin
        clk = 0;
        forever #(CLOCK_PERIOD/2) clk = ~clk;
    end

    // 测试用例
    initial begin
        $dumpfile("counter_simulation.vcd");
        $dumpvars(0, testbench_counter);

        // 测试用例 1: 基本计数功能
        rst = 0;
        enable = 1;
        #20;
        if (count !== 4'b0010) $display("Test case 1 failed at T=20ns, count=%b", count);
        else $display("Test case 1 passed at T=20ns");

        // 测试用例 2: 复位功能测试
        rst = 1;
        #10;
        if (count !== 4'b0000) $display("Test case 2 failed at T=30ns, count=%b", count);
        else $display("Test case 2 passed at T=30ns");

        // 测试用例 3: 边界条件测试 (最大值回绕)
        rst = 0;
        #160;  // 从 T=30ns 到 T=190ns，共 160ns，应计数到 15（4'b1111）并回绕
        if (count !== 4'b0000) $display("Test case 3 failed at T=190ns, count=%b", count);
        else $display("Test case 3 passed at T=190ns");

        // 测试用例 4: 禁用功能测试
        enable = 0;
        #20;
        if (count !== 4'b1111) $display("Test case 4 failed at T=210ns, count=%b", count);
        else $display("Test case 4 passed at T=210ns");

        $finish;
    end
endmodule