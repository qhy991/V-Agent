以下是一个完整的 **Verilog 测试台 (testbench)**，用于验证 `sync_fifo` 模块的功能。假设 `sync_fifo` 是一个同步 FIFO 缓冲器，具有以下接口：

- `clk`: 时钟输入
- `rst_n`: 复位信号（低电平有效）
- `wr_en`: 写使能
- `rd_en`: 读使能
- `din`: 数据输入
- `dout`: 数据输出
- `full`: FIFO 满标志
- `empty`: FIFO 空标志
- `count`: 当前 FIFO 中的数据个数

---

### ✅ 完整的测试台代码如下：

```verilog
`timescale 1ns / 1ps

module tb_sync_fifo;

    // 1. 信号声明
    reg clk;
    reg rst_n;
    reg wr_en;
    reg rd_en;
    reg [7:0] din;
    wire [7:0] dout;
    wire full;
    wire empty;
    wire [7:0] count;

    // 2. 时钟和复位生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns 周期
    end

    initial begin
        rst_n = 0;
        wr_en = 0;
        rd_en = 0;
        din = 8'h00;
        #20; // 等待两个时钟周期
        rst_n = 1;
        #20;
    end

    // 3. 被测模块实例化
    sync_fifo uut (
        .clk(clk),
        .rst_n(rst_n),
        .wr_en(wr_en),
        .rd_en(rd_en),
        .din(din),
        .dout(dout),
        .full(full),
        .empty(empty),
        .count(count)
    );

    // 4. 测试激励生成
    initial begin
        $monitor("Time=%0t | rst_n=%b | wr_en=%b | rd_en=%b | din=0x%02h | dout=0x%02h | full=%b | empty=%b | count=%0d",
                 $time, rst_n, wr_en, rd_en, din, dout, full, empty, count);

        // 初始状态检查
        #20;
        $display("Initial state after reset:");
        $display("full = %b", full);
        $display("empty = %b", empty);
        $display("count = %d", count);

        // 测试写操作
        $display("Testing write operations...");
        wr_en = 1;
        rd_en = 0;
        din = 8'hAA;
        #10;
        din = 8'hBB;
        #10;
        din = 8'hCC;
        #10;
        din = 8'hDD;
        #10;
        din = 8'hEE;
        #10;
        din = 8'hFF;
        #10;

        // 写满后尝试继续写入
        $display("FIFO is full now. Trying to write more data...");
        #10;
        wr_en = 0;
        #10;

        // 测试读操作
        $display("Testing read operations...");
        rd_en = 1;
        wr_en = 0;
        #10;
        #10;
        #10;
        #10;
        #10;
        #10;

        // 读空后尝试读取
        $display("FIFO is empty now. Trying to read more data...");
        #10;
        rd_en = 0;
        #10;

        // 结束仿真
        #1000;
        $finish;
    end

    // 5. 结果检查和显示
    initial begin
        // 检查复位后的状态
        #20;
        if (!full) $display("PASS: full is 0 after reset");
        else $display("FAIL: full should be 0 after reset");

        if (empty) $display("PASS: empty is 1 after reset");
        else $display("FAIL: empty should be 1 after reset");

        if (count == 0) $display("PASS: count is 0 after reset");
        else $display("FAIL: count should be 0 after reset");

        // 检查写入数据后状态
        #100;
        if (!full) $display("PASS: full is 0 after writing 6 items");
        else $display("FAIL: full should be 0 after writing 6 items");

        if (!empty) $display("PASS: empty is 0 after writing 6 items");
        else $display("FAIL: empty should be 0 after writing 6 items");

        if (count == 6) $display("PASS: count is 6 after writing 6 items");
        else $display("FAIL: count should be 6 after writing 6 items");

        // 检查读取数据后状态
        #100;
        if (full) $display("PASS: full is 1 after reading 6 items");
        else $display("FAIL: full should be 1 after reading 6 items");

        if (empty) $display("PASS: empty is 1 after reading 6 items");
        else $display("FAIL: empty should be 1 after reading 6 items");

        if (count == 0) $display("PASS: count is 0 after reading 6 items");
        else $display("FAIL: count should be 0 after reading 6 items");

        // 检查最后状态
        #100;
        if (!full) $display("PASS: full is 0 at the end of simulation");
        else $display("FAIL: full should be 0 at the end of simulation");

        if (empty) $display("PASS: empty is 1 at the end of simulation");
        else $display("FAIL: empty should be 1 at the end of simulation");

        if (count == 0) $display("PASS: count is 0 at the end of simulation");
        else $display("FAIL: count should be 0 at the end of simulation");
    end

endmodule
```

---

### 🔍 说明：

- **时钟周期**：10ns（通过 `#5` 实现）。
- **仿真时间**：1000 个时钟周期（通过 `#1000` 控制）。
- **测试场景**：
  - 复位功能：`rst_n` 为低时，`empty=1`, `full=0`, `count=0`。
  - 写操作：在 `wr_en=1` 且 `!full` 时写入数据。
  - 读操作：在 `rd_en=1` 且 `!empty` 时读出数据。
  - 状态标志：`empty` 和 `full` 在相应条件下正确变化。
  - `count` 输出实时显示当前 FIFO 中的数据个数。

---

### 🧪 可选增强建议：

- 如果你有具体的 `sync_fifo` 模块代码，可以进一步优化测试用例，例如：
  - 验证 FIFO 的深度（如 8 个字节）。
  - 测试不同写/读模式（如连续写、间断写、连续读等）。
  - 添加波形查看器（如使用 ModelSim 或 VCS）进行可视化调试。

如果你提供 `sync_fifo` 的具体实现代码，我可以为你定制更精确的测试台。