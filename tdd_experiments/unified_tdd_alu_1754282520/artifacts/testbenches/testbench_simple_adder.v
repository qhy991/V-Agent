`timescale 1ns/1ps

module tb_simple_adder;

  // 信号声明
  reg a, b;
  wire sum;
  
  // 时钟信号
  reg clk;
  
  // 测试控制信号
  integer i;
  integer test_case;
  
  // 被测模块实例化
  simple_adder uut (
    .a(a),
    .b(b),
    .sum(sum)
  );
  
  // 时钟生成
  always #5.0 clk = ~clk;
  
  // 测试报告变量
  integer pass_count;
  integer fail_count;
  
  // VCD波形文件生成
  initial begin
    $dumpfile("simple_adder.vcd");
    $dumpvars(0, tb_simple_adder);
  end
  
  // 测试激励和验证
  initial begin
    // 初始化
    a = 0;
    b = 0;
    clk = 0;
    test_case = 0;
    pass_count = 0;
    fail_count = 0;
    
    // 显示测试开始信息
    $display("===================================");
    $display("Simple Adder Testbench Started");
    $display("===================================");
    
    // 基本功能测试 (basic_test)
    $display("Starting basic_test...");
    test_case = 1;
    
    // 测试所有可能的输入组合
    for (i = 0; i < 4; i = i + 1) begin
      a = i[1];
      b = i[0];
      
      // 等待时钟上升沿
      @(posedge clk);
      
      // 验证结果
      if (sum == (a ^ b)) begin
        $display("basic_test: a=%b, b=%b, sum=%b - PASS", a, b, sum);
        pass_count = pass_count + 1;
      end else begin
        $display("basic_test: a=%b, b=%b, sum=%b - FAIL", a, b, sum);
        fail_count = fail_count + 1;
      end
    end
    
    // 边界条件测试 (corner_test)
    $display("Starting corner_test...");
    test_case = 2;
    
    // 测试边界值
    a = 0;
    b = 0;
    @(posedge clk);
    if (sum == (a ^ b)) begin
      $display("corner_test: a=%b, b=%b, sum=%b - PASS", a, b, sum);
      pass_count = pass_count + 1;
    end else begin
      $display("corner_test: a=%b, b=%b, sum=%b - FAIL", a, b, sum);
      fail_count = fail_count + 1;
    end
    
    a = 1;
    b = 1;
    @(posedge clk);
    if (sum == (a ^ b)) begin
      $display("corner_test: a=%b, b=%b, sum=%b - PASS", a, b, sum);
      pass_count = pass_count + 1;
    end else begin
      $display("corner_test: a=%b, b=%b, sum=%b - FAIL", a, b, sum);
      fail_count = fail_count + 1;
    end
    
    a = 0;
    b = 1;
    @(posedge clk);
    if (sum == (a ^ b)) begin
      $display("corner_test: a=%b, b=%b, sum=%b - PASS", a, b, sum);
      pass_count = pass_count + 1;
    end else begin
      $display("corner_test: a=%b, b=%b, sum=%b - FAIL", a, b, sum);
      fail_count = fail_count + 1;
    end
    
    a = 1;
    b = 0;
    @(posedge clk);
    if (sum == (a ^ b)) begin
      $display("corner_test: a=%b, b=%b, sum=%b - PASS", a, b, sum);
      pass_count = pass_count + 1;
    end else begin
      $display("corner_test: a=%b, b=%b, sum=%b - FAIL", a, b, sum);
      fail_count = fail_count + 1;
    end
    
    // 显示测试结果
    $display("===================================");
    $display("Test Results Summary:");
    $display("Total Tests: %d", pass_count + fail_count);
    $display("Passed: %d", pass_count);
    $display("Failed: %d", fail_count);
    
    if (fail_count == 0) begin
      $display("Overall Result: PASSED");
    end else begin
      $display("Overall Result: FAILED");
    end
    
    $display("===================================");
    
    // 结束仿真
    $finish;
  end
  
  // 监控信号变化
  initial begin
    $monitor("Time=%0t: a=%b, b=%b, sum=%b", $time, a, b, sum);
  end
  
endmodule