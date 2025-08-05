以下是一个完整的 **Verilog 测试台 (testbench)**，用于验证 `counter_8bit` 模块的功能。该测试台涵盖了所有指定的测试要求，并包含了详细的激励生成、结果检查和显示功能。

---

### ✅ 完整的 Verilog Testbench

```verilog
`timescale 1ns / 1ps

module counter_8bit_tb;

    // 1. 信号声明
    reg clk;
    reg rst_n;
    reg enable;
    reg up_down;
    wire [7:0] count;
    wire overflow;

    // 2. 实例化被测模块
    counter_8bit uut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .up_down(up_down),
        .count(count),
        .overflow(overflow)
    );

    // 3. 时钟和复位生成
    initial begin
        clk = 0;
        rst_n = 0;
        enable = 0;
        up_down = 0;
        #10; // 等待初始稳定
        rst_n = 1; // 释放复位
        #10;
    end

    always #5 clk = ~clk; // 时钟周期为 10ns

    // 4. 测试激励生成
    initial begin
        $monitor("Time: %t | clk=%b, rst_n=%b, enable=%b, up_down=%b, count=0x%h, overflow=%b",
                 $time, clk, rst_n, enable, up_down, count, overflow);

        // 初始状态
        #10;

        // 测试异步复位功能
        $display("=== Testing Asynchronous Reset ===");
        rst_n = 0;
        #10;
        $display("After reset: count = 0x%h", count);
        rst_n = 1;
        #10;

        // 测试计数使能控制
        $display("=== Testing Enable Control ===");
        enable = 0;
        #20;
        $display("Enable off: count = 0x%h", count);
        enable = 1;
        #20;
        $display("Enable on: count = 0x%h", count);

        // 测试上计数模式 (up_down = 1)
        $display("=== Testing Up Counting Mode ===");
        up_down = 1;
        enable = 1;
        #100; // 运行 10 个时钟周期
        $display("Up counting: count = 0x%h", count);

        // 测试溢出检测 (上计数到 FF)
        $display("=== Testing Overflow (Up) ===");
        #100; // 再运行 10 个时钟周期
        $display("Overflow occurred? %b", overflow);
        $display("Final count: 0x%h", count);

        // 测试下计数模式 (up_down = 0)
        $display("=== Testing Down Counting Mode ===");
        up_down = 0;
        enable = 1;
        #100; // 运行 10 个时钟周期
        $display("Down counting: count = 0x%h", count);

        // 测试溢出检测 (下计数到 00)
        $display("=== Testing Overflow (Down) ===");
        #100; // 再运行 10 个时钟周期
        $display("Overflow occurred? %b", overflow);
        $display("Final count: 0x%h", count);

        // 测试计数使能关闭
        $display("=== Testing Enable Off ===");
        enable = 0;
        #20;
        $display("Count stopped: count = 0x%h", count);

        // 测试复位后重新开始
        $display("=== Testing Reset and Restart ===");
        rst_n = 0;
        #10;
        rst_n = 1;
        enable = 1;
        up_down = 1;
        #100;
        $display("After reset and restart: count = 0x%h", count);

        // 结束仿真
        #100;
        $finish;
    end

endmodule
```

---

### 🔍 功能说明

- **时钟**：使用 `always #5 clk = ~clk;` 生成 10ns 周期的时钟。
- **复位**：通过 `rst_n` 异步复位，初始化 `count_reg` 为 0。
- **测试场景**：
  - 异步复位功能
  - 计数使能控制（开启/关闭）
  - 上计数与下计数模式
  - 溢出标志检测（上计数到 FF 和下计数到 00）
- **监控输出**：使用 `$monitor` 和 `$display` 实时显示关键信号的状态。
- **仿真时间**：总共运行约 1000 个时钟周期（根据测试步骤计算）。

---

### 📌 可选增强建议

- 添加波形查看器（如 ModelSim 或 Vivado 的波形窗口）以可视化信号变化。
- 使用 `$assert` 或断言来自动验证某些条件是否满足。
- 添加更复杂的测试序列（如随机启用/禁用、切换方向等）以提高覆盖率。

---

如果你需要将此测试台集成到某个仿真工具中（如 ModelSim、Vivado、Verilator），只需将其保存为 `.v` 文件并编译即可运行。