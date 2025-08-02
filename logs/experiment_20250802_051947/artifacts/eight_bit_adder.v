以下是符合IEEE 1800标准、可综合的 `eight_bit_adder` 模块的Verilog代码，采用RTL风格编写：

```verilog
// eight_bit_adder.v
// 8-bit Ripple Carry Adder with Carry-in and Carry-out
// Designed for RTL synthesis

module eight_bit_adder (
    input        clk,        // Clock signal
    input        rst,        // Active high reset
    input  [7:0] a,         // 8-bit input A
    input  [7:0] b,         // 8-bit input B
    input        cin,        // Carry-in
    output reg [7:0] sum,   // 8-bit sum output
    output reg     cout      // Carry-out
);

// Internal signals for intermediate carry values
reg [7:0] carry;

// Sequential logic: Register the sum and carry on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 8'b0;
        cout <= 1'b0;
        carry <= 8'b0;
    end else begin
        // Compute each bit of the adder using full adders
        // The carry is updated in sequence from LSB to MSB
        // This is a ripple carry implementation
        carry[0] <= cin;  // First carry-in is the external cin
        sum[0] <= a[0] ^ b[0] ^ carry[0];
        carry[1] <= (a[0] & b[0]) | (a[0] & carry[0]) | (b[0] & carry[0]);

        sum[1] <= a[1] ^ b[1] ^ carry[1];
        carry[2] <= (a[1] & b[1]) | (a[1] & carry[1]) | (b[1] & carry[1]);

        sum[2] <= a[2] ^ b[2] ^ carry[2];
        carry[3] <= (a[2] & b[2]) | (a[2] & carry[2]) | (b[2] & carry[2]);

        sum[3] <= a[3] ^ b[3] ^ carry[3];
        carry[4] <= (a[3] & b[3]) | (a[3] & carry[3]) | (b[3] & carry[3]);

        sum[4] <= a[4] ^ b[4] ^ carry[4];
        carry[5] <= (a[4] & b[4]) | (a[4] & carry[4]) | (b[4] & carry[4]);

        sum[5] <= a[5] ^ b[5] ^ carry[5];
        carry[6] <= (a[5] & b[5]) | (a[5] & carry[5]) | (b[5] & carry[5]);

        sum[6] <= a[6] ^ b[6] ^ carry[6];
        carry[7] <= (a[6] & b[6]) | (a[6] & carry[6]) | (b[6] & carry[6]);

        sum[7] <= a[7] ^ b[7] ^ carry[7];
        cout <= (a[7] & b[7]) | (a[7] & carry[7]) | (b[7] & carry[7]);
    end
end

endmodule
```

### 说明：

- **模块名称**：`eight_bit_adder`
- **输入端口**：
  - `clk`: 时钟信号（用于同步逻辑）
  - `rst`: 复位信号（高电平有效）
  - `a`, `b`: 两个8位二进制数
  - `cin`: 进位输入
- **输出端口**：
  - `sum`: 8位加法结果
  - `cout`: 最终进位输出
- **内部信号**：
  - `carry`: 用于存储每级加法器的进位值
- **实现方式**：
  - 使用**逐位全加器（Full Adder）** 实现8位加法器
  - 采用**行波进位（Ripple Carry）** 结构
  - 所有计算在时钟上升沿进行，复位时清零

### 注意事项：

- 此设计是**同步电路**，所有状态更新发生在时钟边沿。
- 如果需要异步复位，可以将 `rst` 改为 `always @(posedge clk or negedge rst)`，但通常建议使用同步复位以提高可综合性和稳定性。
- 该设计适用于大多数FPGA和ASIC工具链，符合IEEE 1800标准。