以下是符合IEEE 1800标准、可综合的 `simple_8bit_adder` 模块的Verilog代码，采用行为级（behavioral）风格实现：

```verilog
// simple_8bit_adder.v
// 8-bit binary adder with carry-in and carry-out
// Behavioral style implementation
// Supports clocked operation with active-high reset

module simple_8bit_adder (
    input        clk,        // Clock signal
    input        rst,        // Active high reset
    input  [7:0] a,         // First 8-bit operand
    input  [7:0] b,         // Second 8-bit operand
    input        cin,        // Carry-in
    output reg [7:0] sum,   // Sum result (8 bits)
    output reg     cout      // Carry-out
);

    // Internal signals for intermediate results
    reg [8:0] full_adder_result;  // 9-bit result to capture carry

    // Synchronous process: triggered on positive edge of clock
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            // Reset all outputs to 0
            sum <= 8'b0;
            cout <= 1'b0;
        end else begin
            // Perform 8-bit addition with carry-in
            full_adder_result <= {1'b0, a} + {1'b0, b} + cin;
            
            // Extract the 8-bit sum from the 9-bit result
            sum <= full_adder_result[7:0];
            
            // Carry-out is the 9th bit of the result
            cout <= full_adder_result[8];
        end
    end

endmodule
```

### 说明：

- **模块功能**：该模块实现一个8位二进制加法器，支持输入进位 `cin` 和输出进位 `cout`。
- **时钟和复位**：使用同步复位（`rst` 为高电平有效），在时钟上升沿触发计算。
- **内部信号**：使用一个9位寄存器 `full_adder_result` 来存储加法结果，以便提取进位。
- **行为级实现**：通过简单的加法运算完成逻辑，适用于综合工具处理。
- **可综合性**：代码中没有使用非综合的语句（如 `initial` 或 `fork/join`），适合用于FPGA或ASIC设计。

如需进一步扩展为流水线结构或使用门级建模，请告知。