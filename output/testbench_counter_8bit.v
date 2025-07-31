module testbench_counter_8bit;

    // 信号声明
    reg clk;
    reg rst;
    reg en;
    wire [7:0] count;

    // 实例化被测模块
    counter_8bit uut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .count(count)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns周期
    end

    // 测试控制
    initial begin
        $dumpfile("testbench_counter_8bit.vcd");
        $dumpvars(0, testbench_counter_8bit);

        // 初始化
        rst = 0;
        en = 0;
        #20;
        rst = 1;
        #20;

        // 基本功能测试：计数器从0到255
        $display("\n=== Basic Function Test ===");
        en = 1;
        for (int i = 0; i < 256; i++) begin
            #10;
            $display("Count = %d", count);
            if (count != i) begin
                $display("[ERROR] Count mismatch at cycle %d: Expected %d, Got %d", i, i, count);
            end
        end

        // 边界值测试：最大值和最小值
        $display("\n=== Boundary Value Test ===");
        #10;
        $display("Count = %d (Max value)", count);
        if (count != 255) begin
            $display("[ERROR] Max value mismatch: Expected 255, Got %d", count);
        end

        #10;
        $display("Count = %d (After overflow)", count);
        if (count != 0) begin
            $display("[ERROR] Overflow mismatch: Expected 0, Got %d", count);
        end

        // 随机测试：随机触发复位
        $display("\n=== Random Test ===");
        en = 1;
        for (int i = 0; i < 10; i++) begin
            #10;
            if ($random() % 2 == 0) begin
                rst = 0;
                #10;
                rst = 1;
                $display("Reset triggered at cycle %d", i);
            end
        end

        // 性能测试：计数器运行一段时间
        $display("\n=== Performance Test ===");
        #1000;
        $display("Count after 1000 cycles = %d", count);

        // 结束仿真
        $finish;
    end

endmodule