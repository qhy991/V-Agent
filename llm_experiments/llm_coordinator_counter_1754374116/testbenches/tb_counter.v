module tb_counter;
  // 时钟和复位信号
  reg clk;
  reg rst;

  // 假设被测 counter 模块的接口如下：
  reg enable;
  reg [3:0] count_value;

  // 实例化被测 counter 模块
  counter uut (
    .clk(clk),
    .rst(rst),
    .enable(enable),
    .count_value(count_value)
  );

  // 生成时钟：50%占空比，周期为10时间单位
  always begin
    #5 clk = ~clk;
  end

  // 初始化测试平台
  initial begin
    // 初始化信号
    clk = 0;
    rst = 0;
    enable = 0;

    // 施加复位
    #10 rst = 1;
    #10 rst = 0;

    // 测试1：复位后计数器应为0
    if (count_value === 4'd0) begin
      $display("PASS: Counter reset to 0");
    end else begin
      $error("FAIL: Counter did not reset properly");
    end

    // 测试2：启用计数，运行16个时钟周期
    enable = 1;
    repeat (16) begin
      @ (posedge clk);
    end

    // 检查是否回绕到0（假设为4位递增计数器）
    if (count_value === 4'd0) begin
      $display("PASS: Counter wrapped around correctly");
    end else begin
      $error("FAIL: Counter did not wrap correctly, got %d", count_value);
    end

    // 测试3：禁用使能，检查值保持不变
    enable = 0;
    @ (posedge clk);
    #1;
    if (count_value === 4'd0) begin
      $display("PASS: Counter held value when disabled");
    end else begin
      $error("FAIL: Counter changed when enable was low");
    end

    // 测试4：重新启用，应从保持值继续
    enable = 1;
    @ (posedge clk);
    if (count_value === 4'd1) begin
      $display("PASS: Counter resumed counting correctly");
    end else begin
      $error("FAIL: Counter did not resume from correct value");
    end

    // 结束仿真
    $display("Simulation completed.");
    $finish;
  end

endmodule