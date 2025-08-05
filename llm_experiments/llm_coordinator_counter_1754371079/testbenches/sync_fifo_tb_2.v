以下是为 `sync_fifo` 模块生成的完整 **Verilog 测试台 (testbench)**，满足您提出的所有测试要求：

---

### ✅ 1. Testbench 模块声明

```verilog
module tb_sync_fifo;

    // 参数定义（根据实际模块参数调整）
    parameter DATA_WIDTH = 8;
    parameter DEPTH = 16;

    // 信号声明
    reg clk;
    reg rst_n;
    reg wr_en;
    reg rd_en;
    reg [DATA_WIDTH-1:0] din;
    wire [DATA_WIDTH-1:0] dout;
    wire empty;
    wire full;
    wire [DATA_WIDTH-1:0] count;

    // 实例化被测模块
    sync_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH(DEPTH)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .wr_en(wr_en),
        .rd_en(rd_en),
        .din(din),
        .dout(dout),
        .empty(empty),
        .full(full),
        .count(count)
    );

    // 时钟和复位生成
    initial begin
        clk = 0;
        rst_n = 0;
        wr_en = 0;
        rd_en = 0;
        din = 0;
        #10; // 等待初始稳定
        rst_n = 1; // 释放复位
        #10;
    end

    always #5 clk = ~clk; // 10ns 周期时钟

    // 监控信号变化
    initial begin
        $monitor("Time=%0t, rst_n=%b, wr_en=%b, rd_en=%b, din=0x%h, dout=0x%h, empty=%b, full=%b, count=%0d",
                 $time, rst_n, wr_en, rd_en, din, dout, empty, full, count);
    end

    // 测试激励生成
    initial begin
        // 初始状态
        wr_en = 0;
        rd_en = 0;
        din = 0;

        // 复位测试
        $display("=== Testing Reset ===");
        rst_n = 0;
        #20;
        $display("After reset: empty=%b, full=%b, count=%0d", empty, full, count);
        #20;

        // 释放复位
        rst_n = 1;
        #20;

        // 写入数据测试
        $display("=== Writing Data ===");
        for (int i = 0; i < DEPTH; i++) begin
            din = i;
            wr_en = 1;
            rd_en = 0;
            #10;
            $display("Write %0d: din=0x%h, full=%b, count=%0d", i, din, full, count);
        end
        wr_en = 0;

        // 读取数据测试
        $display("=== Reading Data ===");
        for (int i = 0; i < DEPTH; i++) begin
            rd_en = 1;
            wr_en = 0;
            #10;
            $display("Read %0d: dout=0x%h, empty=%b, count=%0d", i, dout, empty, count);
        end
        rd_en = 0;

        // 写满后尝试写入
        $display("=== Full FIFO Test ===");
        wr_en = 1;
        #10;
        $display("Write after full: full=%b, count=%0d", full, count);

        // 读空后尝试读取
        $display("=== Empty FIFO Test ===");
        rd_en = 1;
        #10;
        $display("Read after empty: empty=%b, count=%0d", empty, count);

        // 继续仿真 1000 个时钟周期
        #10000; // 1000 * 10ns = 10,000ns

        $display("=== Simulation Finished ===");
        $finish;
    end

    // 结果检查
    initial begin
        // 可以添加更详细的断言或检查逻辑
        // 例如：检查在复位后 empty 应该为 1
        #10;
        if (empty !== 1) $display("ERROR: After reset, empty should be 1, but is %b", empty);
        if (full !== 0) $display("ERROR: After reset, full should be 0, but is %b", full);
        if (count !== 0) $display("ERROR: After reset, count should be 0, but is %0d", count);

        // 在写入后检查 count 是否递增
        #20;
        if (count !== 1) $display("ERROR: After first write, count should be 1, but is %0d", count);

        // 在读取后检查 count 是否递减
        #20;
        if (count !== DEPTH - 1) $display("ERROR: After first read, count should be %0d, but is %0d", DEPTH - 1, count);

        // 更多检查可以在此处添加...
    end

endmodule
```

---

### ✅ 2. 说明与注意事项

- **参数支持**：测试台使用了 `DATA_WIDTH` 和 `DEPTH` 参数，确保与 `sync_fifo` 模块一致。
- **时钟周期**：`#5` 表示 5ns 的时钟边沿，总周期为 10ns。
- **仿真时间**：通过 `#10000` 实现 1000 个时钟周期（10ns × 1000 = 10,000ns）。
- **$monitor 和 $display**：用于实时监控和输出关键信号的状态。
- **测试场景覆盖**：
  - 复位功能验证
  - 写操作验证
  - 读操作验证
  - 状态标志（empty/full）验证
  - 数据计数器（count）验证

---

### ✅ 3. 使用建议

- 将此测试台保存为 `tb_sync_fifo.v`。
- 确保 `sync_fifo.v` 已正确实现并编译。
- 使用仿真工具（如 ModelSim、VCS、Verilator 等）运行测试。

---

如果您提供 `sync_fifo` 的具体代码，我可以进一步优化测试台以匹配其内部逻辑。