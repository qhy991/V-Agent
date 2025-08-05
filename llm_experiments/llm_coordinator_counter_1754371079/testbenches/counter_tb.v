module counter_tb;

    // 定义时钟周期
    parameter CLK_PERIOD = 10;

    // 信号声明
    reg clk;           // 时钟信号
    reg rst;           // 复位信号，高电平有效
    reg enable;        // 使能信号
    wire [7:0] count;  // 计数器输出

    // 实例化被测模块 counter
    counter uut (
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .count(count)
    );

    // 生成周期为10ns的时钟信号
    always begin
        clk = 0;
        #(CLK_PERIOD/2);
        clk = 1;
        #(CLK_PERIOD/2);
    end

    // 测试激励生成
    initial begin
        // 初始化输入信号
        rst = 1;
        enable = 0;

        $display("Starting counter testbench...");

        // 测试阶段1: 复位功能测试（复位期间计数器应为0）
        $display("Test 1: Reset functionality");
        @(posedge clk);
        @(posedge clk);
        if (count == 8'd0) begin
            $display("PASS: Counter is reset to 0");
        end else begin
            $display("FAIL: Counter did not reset correctly");
        end

        // 释放复位
        rst = 0;
        @(posedge clk);
        @(posedge clk);

        // 测试阶段2: 使能为低时，计数器保持不变
        $display("Test 2: Enable low - counter should hold value");
        if (count == 8'd0) begin
            $display("PASS: Counter remained at 0 when enable is low");
        end else begin
            $display("FAIL: Counter changed when enable was low");
        end

        // 测试阶段3: 使能为高，计数器递增（从0到1）
        enable = 1;
        $display("Test 3: Enable high - counter should increment");
        repeat(5) @(posedge clk);
        if (count == 8'd5) begin
            $display("PASS: Counter incremented correctly from 0");
        end else begin
            $display("FAIL: Counter did not increment properly");
        end

        // 测试阶段4: 验证边界值1和254
        $display("Test 4: Boundary test at value 1 and 254");
        // Advance to 254
        repeat(249) @(posedge clk);
        if (count == 8'd254) begin
            $display("PASS: Counter reached 254 correctly");
        end else begin
            $display("FAIL: Counter failed to reach 254");
        end

        // 下一个时钟应溢出到0
        @(posedge clk);
        if (count == 8'd255) begin
            $display("PASS: Counter reached 255 before overflow");
        end else begin
            $display("FAIL: Counter did not reach 255");
        end

        // 溢出测试
        @(posedge clk);
        if (count == 8'd0) begin
            $display("PASS: Counter overflowed correctly from 255 to 0");
        end else begin
            $display("FAIL: Counter did not overflow to 0");
        end

        // 测试阶段5: 溢出后继续递增
        $display("Test 5: Post-overflow increment");
        repeat(3) @(posedge clk);
        if (count == 8'd3) begin
            $display("PASS: Counter continued incrementing after overflow");
        end else begin
            $display("FAIL: Counter did not continue correctly after overflow");
        end

        // 测试阶段6: 再次测试复位功能（在非零值时复位）
        $display("Test 6: Reset from non-zero state");
        rst = 1;
        @(posedge clk);
        if (count == 8'd0) begin
            $display("PASS: Counter reset to 0 from non-zero state");
        end else begin
            $display("FAIL: Counter did not reset to 0 when rst=1");
        end

        // 结束仿真
        $display("Counter testbench completed.");
        $finish;
    end

endmodule