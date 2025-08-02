以下是为您提供的专业Verilog测试台，满足所有指定要求：

```verilog
`timescale 1ns / 1ps

module task_tb;

    // 时钟周期定义
    parameter CLK_PERIOD = 10.0ns;

    // 信号声明
    reg [7:0] a;
    reg [7:0] b;
    reg       cin;
    wire [7:0] sum;
    wire       cout;

    // 时钟和复位信号
    reg clk;
    reg rst_n;

    // 被测模块实例化
    task uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    // 全加器模块实例化（在测试台中不需要，因为是内部模块）
    // full_adder fa ( ... ) 无需在此处实例化

    // 波形转储设置
    initial begin
        $dumpfile("task_tb.vcd");
        $dumpvars(0, task_tb);
    end

    // 时钟生成
    initial begin
        clk = 0;
        forever begin
            # (CLK_PERIOD/2) clk = ~clk;
        end
    end

    // 复位生成
    initial begin
        rst_n = 0;
        # (CLK_PERIOD * 2); // 等待两个时钟周期
        rst_n = 1;
    end

    // 测试激励生成
    initial begin
        // 初始化输入
        a = 8'h00;
        b = 8'h00;
        cin = 1'b0;

        // 启用覆盖率收集
        $coverage_on();

        // 测试用例1: 0 + 0 + 0 = 0, no carry
        # (CLK_PERIOD * 1);
        a = 8'h00;
        b = 8'h00;
        cin = 1'b0;
        # (CLK_PERIOD * 1);
        $display("Test Case 1: 0 + 0 + 0 = 0, no carry");
        $monitor("Time=%0t, a=0x%02h, b=0x%02h, cin=%b, sum=0x%02h, cout=%b", $time, a, b, cin, sum, cout);

        // 验证结果
        assert (sum == 8'h00 && cout == 1'b0)
            $display("Test Case 1 Passed");
        else
            $display("Test Case 1 Failed");

        // 测试用例2: 0xFF + 0x01 + 0 = 0x00, carry=1
        # (CLK_PERIOD * 1);
        a = 8'hFF;
        b = 8'h01;
        cin = 1'b0;
        # (CLK_PERIOD * 1);
        $display("Test Case 2: 0xFF + 0x01 + 0 = 0x00, carry=1");
        $monitor("Time=%0t, a=0x%02h, b=0x%02h, cin=%b, sum=0x%02h, cout=%b", $time, a, b, cin, sum, cout);

        // 验证结果
        assert (sum == 8'h00 && cout == 1'b1)
            $display("Test Case 2 Passed");
        else
            $display("Test Case 2 Failed");

        // 测试用例3: 0x7F + 0x80 + 0 = 0xFF, no carry
        # (CLK_PERIOD * 1);
        a = 8'h7F;
        b = 8'h80;
        cin = 1'b0;
        # (CLK_PERIOD * 1);
        $display("Test Case 3: 0x7F + 0x80 + 0 = 0xFF, no carry");
        $monitor("Time=%0t, a=0x%02h, b=0x%02h, cin=%b, sum=0x%02h, cout=%b", $time, a, b, cin, sum, cout);

        // 验证结果
        assert (sum == 8'hFF && cout == 1'b0)
            $display("Test Case 3 Passed");
        else
            $display("Test Case 3 Failed");

        // 测试用例4: 0x00 + 0x00 + 1 = 0x01, no carry
        # (CLK_PERIOD * 1);
        a = 8'h00;
        b = 8'h00;
        cin = 1'b1;
        # (CLK_PERIOD * 1);
        $display("Test Case 4: 0x00 + 0x00 + 1 = 0x01, no carry");
        $monitor("Time=%0t, a=0x%02h, b=0x%02h, cin=%b, sum=0x%02h, cout=%b", $time, a, b, cin, sum, cout);

        // 验证结果
        assert (sum == 8'h01 && cout == 1'b0)
            $display("Test Case 4 Passed");
        else
            $display("Test Case 4 Failed");

        // 测试用例5: 0x00 + 0xFF + 1 = 0x00, carry=1
        # (CLK_PERIOD * 1);
        a = 8'h00;
        b = 8'hFF;
        cin = 1'b1;
        # (CLK_PERIOD * 1);
        $display("Test Case 5: 0x00 + 0xFF + 1 = 0x00, carry=1");
        $monitor("Time=%0t, a=0x%02h, b=0x%02h, cin=%b, sum=0x%02h, cout=%b", $time, a, b, cin, sum, cout);

        // 验证结果
        assert (sum == 8'h00 && cout == 1'b1)
            $display("Test Case 5 Passed");
        else
            $display("Test Case 5 Failed");

        // 模拟10000个时钟周期
        for (int i = 0; i < 10000; i++) begin
            # (CLK_PERIOD);
        end

        // 结束仿真
        $display("Simulation completed.");
        $finish;
    end

    // 测试报告生成
    initial begin
        # (CLK_PERIOD * 10000);
        $display("Coverage Report:");
        $coverage_report();
    end

endmodule
```

### 说明：

1. **testbench模块声明**：
   - 使用 `module task_tb;` 声明测试台模块。

2. **信号声明**：
   - 包括输入信号 `a`, `b`, `cin` 和输出信号 `sum`, `cout`。
   - 添加了时钟 `clk` 和复位 `rst_n` 信号。

3. **时钟和复位生成逻辑**：
   - `clk` 以 10.0ns 的周期翻转。
   - `rst_n` 在开始时拉低，然后在两个时钟周期后释放。

4. **被测模块的实例化**：
   - 实例化了 `task` 模块，并连接了所有必要的信号。

5. **测试激励生成**：
   - 每个测试用例都设置了不同的输入值，并等待一个时钟周期以确保计算完成。

6. **结果检查和断言**：
   - 使用 `assert` 语句验证每个测试用例的结果是否符合预期。

7. **$display、$monitor 和 $finish**：
   - `$display` 用于显示测试信息。
   - `$monitor` 用于实时监控关键信号。
   - `$finish` 用于结束仿真。

8. **波形转储设置（VCD文件）**：
   - 使用 `$dumpfile` 和 `$dumpvars` 生成 VCD 文件，便于后续分析。

9. **测试报告生成**：
   - 使用 `$coverage_report()` 显示覆盖率信息。

### 注意事项：

- 该测试台使用了 `assert` 语句进行功能验证，但需要确保仿真工具支持断言功能。
- 如果使用的是非标准仿真器，可以将 `assert` 替换为 `if` 语句并打印错误信息。
- 可根据实际需求调整测试用例的数量和内容。