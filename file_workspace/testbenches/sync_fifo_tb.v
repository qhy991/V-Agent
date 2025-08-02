以下是为 `sync_fifo` 模块设计的完整 **Verilog 测试台 (testbench)**，满足所有指定的测试要求：

```verilog
`timescale 1ns / 1ps

module tb_sync_fifo;

    // 参数定义（与模块一致）
    parameter DATA_WIDTH = 8;
    parameter FIFO_DEPTH = 16;
    parameter ADDR_WIDTH = 4;

    // 信号声明
    reg clk;
    reg rst_n;
    reg wr_en;
    reg rd_en;
    reg [DATA_WIDTH-1:0] wr_data;
    wire [DATA_WIDTH-1:0] rd_data;
    wire full;
    wire empty;
    wire [ADDR_WIDTH:0] count;

    // 实例化被测模块
    sync_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .FIFO_DEPTH(FIFO_DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .wr_en(wr_en),
        .rd_en(rd_en),
        .wr_data(wr_data),
        .rd_data(rd_data),
        .full(full),
        .empty(empty),
        .count(count)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns 周期
    end

    // 复位生成
    initial begin
        rst_n = 0;
        #10; // 等待10ns复位
        rst_n = 1;
        #10;
    end

    // 监控信号
    initial begin
        $monitor("Time: %t | rst_n=%b | wr_en=%b | rd_en=%b | wr_data=0x%h | rd_data=0x%h | full=%b | empty=%b | count=%d",
                 $time, rst_n, wr_en, rd_en, wr_data, rd_data, full, empty, count);
    end

    // 测试激励生成
    initial begin
        // 初始化输入信号
        wr_en = 0;
        rd_en = 0;
        wr_data = 0;

        // 初始状态检查：复位后
        #20;
        $display("Test 1: Reset Check");
        if (empty) $display("PASS: empty is 1 after reset.");
        else $display("FAIL: empty should be 1 after reset.");
        if (!full) $display("PASS: full is 0 after reset.");
        else $display("FAIL: full should be 0 after reset.");
        if (count == 0) $display("PASS: count is 0 after reset.");
        else $display("FAIL: count should be 0 after reset.");

        // 写入操作测试
        $display("Test 2: Write Operation Test");
        for (int i = 0; i < FIFO_DEPTH; i++) begin
            wr_data = i;
            wr_en = 1;
            rd_en = 0;
            #10;
            if (i < FIFO_DEPTH - 1) begin
                if (!full) $display("PASS: Not full after writing data 0x%x.", i);
                else $display("FAIL: Should not be full yet.");
            end else begin
                if (full) $display("PASS: Full after writing data 0x%x.", i);
                else $display("FAIL: Should be full now.");
            end
            if (count == i + 1) $display("PASS: Count is correct after writing data 0x%x.", i);
            else $display("FAIL: Count is incorrect after writing data 0x%x.", i);
        end
        wr_en = 0;

        // 读取操作测试
        $display("Test 3: Read Operation Test");
        for (int i = 0; i < FIFO_DEPTH; i++) begin
            rd_en = 1;
            wr_en = 0;
            #10;
            if (i < FIFO_DEPTH - 1) begin
                if (!empty) $display("PASS: Not empty after reading data 0x%x.", i);
                else $display("FAIL: Should not be empty yet.");
            end else begin
                if (empty) $display("PASS: Empty after reading data 0x%x.", i);
                else $display("FAIL: Should be empty now.");
            end
            if (count == FIFO_DEPTH - i - 1) $display("PASS: Count is correct after reading data 0x%x.", i);
            else $display("FAIL: Count is incorrect after reading data 0x%x.", i);
            if (rd_data == i) $display("PASS: Read data matches written data 0x%x.", i);
            else $display("FAIL: Read data does not match written data 0x%x.", i);
        end
        rd_en = 0;

        // 满标志测试
        $display("Test 4: Full Flag Test");
        wr_en = 1;
        rd_en = 0;
        wr_data = 0xFF;
        #10;
        if (full) $display("PASS: Full flag is set correctly.");
        else $display("FAIL: Full flag should be set.");
        wr_en = 0;

        // 空标志测试
        $display("Test 5: Empty Flag Test");
        rd_en = 1;
        wr_en = 0;
        #10;
        if (empty) $display("PASS: Empty flag is set correctly.");
        else $display("FAIL: Empty flag should be set.");
        rd_en = 0;

        // 结束仿真
        #1000;
        $finish;
    end

endmodule
```

---

### ✅ **说明**

1. **模块声明**：
   - 使用 `tb_sync_fifo` 作为测试台模块名。
   - 包含了与 `sync_fifo` 模块相同的参数。

2. **信号声明**：
   - 输入信号包括 `clk`, `rst_n`, `wr_en`, `rd_en`, `wr_data`。
   - 输出信号包括 `rd_data`, `full`, `empty`, `count`。

3. **时钟和复位生成**：
   - `clk` 以 10ns 周期运行。
   - `rst_n` 在初始阶段拉低，然后在 10ns 后释放。

4. **实例化被测模块**：
   - 使用 `uut` 实例化 `sync_fifo` 模块，并传递正确的参数。

5. **测试激励生成**：
   - 包括复位、写入、读取、满/空标志等测试场景。
   - 使用循环进行多组数据写入和读取。

6. **结果检查和显示**：
   - 使用 `$display` 和 `$monitor` 显示关键信号的状态。
   - 对每个测试步骤进行判断并输出“PASS”或“FAIL”。

7. **$display 和 $monitor**：
   - `$monitor` 实时监控关键信号的变化。
   - `$display` 用于输出测试结果信息。

---

### 🧪 **测试场景覆盖**

| 测试场景         | 验证内容                         |
|------------------|----------------------------------|
| 复位功能         | `empty=1`, `full=0`, `count=0`   |
| 写入操作         | 数据正确写入，`count` 正确更新   |
| 读取操作         | 数据正确读出，`count` 正确更新   |
| 满标志           | `full=1` 当 `count=FIFO_DEPTH`   |
| 空标志           | `empty=1` 当 `count=0`           |

---

如需进一步扩展（例如加入随机测试、覆盖率分析、波形查看等），可以使用 `vcs` 或 `iverilog` 工具进行仿真。