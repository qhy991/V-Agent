以下是符合IEEE 1800标准、可综合的Verilog模块 `test_module`，满足您提出的功能需求和编码风格要求：

```verilog
// test_module.v
// Verilog module for basic functionality testing
// Designed for RTL synthesis
// Clock domain: clk (positive edge), rst (active high)

module test_module (
    input      clk,        // Clock signal
    input      rst,        // Reset signal (active high)
    input      in_data,    // Input data signal
    output reg out_data   // Output data signal
);

// -------------------------------
// Internal Signals
// -------------------------------
reg [7:0] counter;         // 8-bit counter for demonstration

// -------------------------------
// Main Logic
// -------------------------------
always @(posedge clk or posedge rst) begin
    if (rst) begin
        // Reset condition: clear outputs and counter
        out_data <= 1'b0;
        counter <= 8'h00;
    end else begin
        // Normal operation: increment counter and toggle output
        counter <= counter + 1;
        out_data <= ~out_data;  // Toggle output on each clock cycle
    end
end

// -------------------------------
// Additional Test Logic (Optional)
// -------------------------------
// This section can be used to add more test patterns or signals
// For example, you could add a test pattern generator or status indicators

// Example: Monitor input and output
// This is not synthesizable but useful for simulation
`ifdef SIMULATION
    always @(negedge clk) begin
        $display("Time: %t | in_data = %b | out_data = %b | counter = %h",
                 $time, in_data, out_data, counter);
    end
`endif

endmodule
```

---

### ✅ 功能说明：

- **输入端口**：
  - `clk`: 时钟信号（正边沿触发）
  - `rst`: 复位信号（高电平有效）
  - `in_data`: 输入数据（用于测试或扩展功能）

- **输出端口**：
  - `out_data`: 输出数据（用于验证逻辑）

- **内部逻辑**：
  - 使用一个8位计数器 `counter` 来演示基本行为。
  - 在复位时，清空输出和计数器。
  - 正常运行时，每拍时钟翻转 `out_data` 的状态，并递增计数器。

---

### 📌 注意事项：

- 该模块是**可综合**的，适用于FPGA或ASIC设计。
- `in_data` 可以根据需要扩展为多比特输入或添加其他控制信号。
- 模块中包含了一个仿真用的 `$display` 语句，仅在仿真时启用（通过 `SIMULATION` 宏定义）。

---

如需进一步扩展功能（例如添加状态机、计数器、寄存器等），可以在此基础上进行修改。是否需要我为您生成更复杂的版本？