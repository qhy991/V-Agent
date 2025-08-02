以下是符合IEEE 1800标准、可综合的 `simple_8bit_adder` 模块的Verilog代码，采用行为级（behavioral）风格实现：

```verilog
// simple_8bit_adder.v
// 8-bit binary adder with carry-in and carry-out
// Behavioral style implementation

module simple_8bit_adder (
    input        clk,       // Clock signal
    input        rst,       // Active high reset
    input  [7:0] a,        // First 8-bit operand
    input  [7:0] b,        // Second 8-bit operand
    input        cin,       // Carry-in
    output reg [7:0] sum,   // Sum result
    output reg     cout      // Carry-out
);

    // Internal signals for intermediate results
    reg [7:0] sum_reg;
    reg       cout_reg;

    // Synchronous process: triggered on clock edge
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            // Reset the outputs to zero
            sum_reg <= 8'b0;
            cout_reg <= 1'b0;
        end else begin
            // Perform 8-bit addition with carry-in
            {cout_reg, sum_reg} = a + b + cin;
        end
    end

    // Assign the output registers to the actual output ports
    assign sum = sum_reg;
    assign cout = cout_reg;

endmodule
```

### 说明：

- **模块名称**：`simple_8bit_adder`
- **输入端口**：
  - `clk`: 时钟信号
  - `rst`: 复位信号（高电平有效）
  - `a`, `b`: 8位加数
  - `cin`: 进位输入
- **输出端口**：
  - `sum`: 8位加法结果
  - `cout`: 进位输出
- **内部寄存器**：
  - `sum_reg` 和 `cout_reg` 用于存储当前计算结果，以确保同步行为。
- **功能实现**：
  - 使用 `{cout_reg, sum_reg} = a + b + cin;` 实现加法运算，并将进位和结果分别保存到对应的寄存器中。
- **复位逻辑**：
  - 在复位时，清零 `sum_reg` 和 `cout_reg`。

### 注意事项：

- 此模块是**同步设计**，所有状态变化都发生在时钟上升沿。
- 该代码适用于大多数FPGA或ASIC综合工具，符合IEEE 1800标准。
- 如果需要异步复位，可以调整 `always @(posedge clk or posedge rst)` 为 `always @(posedge clk or negedge rst)`，但需注意时序约束。

如需支持异步复位或增加流水线结构，请告知我进一步优化。