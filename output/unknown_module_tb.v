module unknown_module_tb;

    // 信号声明
    reg clk;
    reg rst_n;
    wire [7:0] count_out;

    // 实例化被测模块
    unknown_module uut (
        .clk(clk),
        .rst_n(rst_n),
        .count_out(count_out)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns周期
    end

    // 测试控制
    initial begin
        $dumpfile("unknown_module_tb.vcd");
        $dumpvars(0, unknown_module_tb);

        // 初始化
        rst_n = 0;
        #20;
        rst_n = 1;
        #20;

        // 基本功能测试：计数器从0到255
        $display("\n=== Basic Function Test ===");
        for (int i = 0; i < 256; i++) begin
            #10;
            $display("Count = %d", count_out);
            if (count_out != i) begin
                $display("[ERROR] Count mismatch at cycle %d: Expected %d, Got %d", i, i, count_out);
            end
        end

        // 边界值测试：最大值和最小值
        $display("\n=== Boundary Value Test ===");
        #10;
        $display("Count = %d (Max value)", count_out);
        if (count_out != 255) begin
            $display("[ERROR] Max value mismatch: Expected 255, Got %d", count_out);
        end

        #10;
        $display("Count = %d (After overflow)", count_out);
        if (count_out != 0) begin
            $display("[ERROR] Overflow mismatch: Expected 0, Got %d", count_out);
        end

        // 随机测试：随机触发复位
        $display("\n=== Random Test ===");
        for (int i = 0; i < 10; i++) begin
            #10;
            if ($random() % 2 == 0) begin
                rst_n = 0;
                #10;
                rst_n = 1;
                $display("Reset triggered at cycle %d", i);
            end
        end

        // 性能测试：计数器运行一段时间
        $display("\n=== Performance Test ===");
        #1000;
        $display("Count after 1000 cycles = %d", count_out);

        // 结束仿真
        $finish;
    end

endmodule