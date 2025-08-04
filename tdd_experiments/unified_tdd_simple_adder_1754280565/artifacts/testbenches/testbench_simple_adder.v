`timescale 1ns/1ps

module tb_simple_adder;

  // 信号声明
  reg a;
  reg b;
  wire sum;
  
  // 时钟信号
  reg clk;
  
  // 测试控制信号
  integer i;
  integer test_case;
  
  // 实例化被测模块
  simple_adder uut (
    .a(a),
    .b(b),
    .sum(sum)
  );
  
  // 时钟生成
  always #5 clk = ~clk;
  
  // 测试报告变量
  integer pass_count;
  integer fail_count;
  
  // 监控信号
  initial begin
    $monitor("Time=%0t: a=%b b=%b sum=%b", $time, a, b, sum);
  end
  
  // VCD波形转储
  initial begin
    $dumpfile("simple_adder.vcd");
    $dumpvars(0, tb_simple_adder);
  end
  
  // 基本功能测试
  task basic_test;
    begin
      $display("=== 开始基本功能测试 ===");
      
      // 测试所有可能的输入组合
      a = 0; b = 0; #10;
      if (sum !== 0) begin
        $display("FAIL: a=0, b=0, expected sum=0, got sum=%b", sum);
        fail_count = fail_count + 1;
      end else begin
        $display("PASS: a=0, b=0, sum=%b", sum);
        pass_count = pass_count + 1;
      end
      
      a = 0; b = 1; #10;
      if (sum !== 1) begin
        $display("FAIL: a=0, b=1, expected sum=1, got sum=%b", sum);
        fail_count = fail_count + 1;
      end else begin
        $display("PASS: a=0, b=1, sum=%b", sum);
        pass_count = pass_count + 1;
      end
      
      a = 1; b = 0; #10;
      if (sum !== 1) begin
        $display("FAIL: a=1, b=0, expected sum=1, got sum=%b", sum);
        fail_count = fail_count + 1;
      end else begin
        $display("PASS: a=1, b=0, sum=%b", sum);
        pass_count = pass_count + 1;
      end
      
      a = 1; b = 1; #10;
      if (sum !== 0) begin
        $display("FAIL: a=1, b=1, expected sum=0, got sum=%b", sum);
        fail_count = fail_count + 1;
      end else begin
        $display("PASS: a=1, b=1, sum=%b", sum);
        pass_count = pass_count + 1;
      end
      
      $display("=== 基本功能测试结束 ===");
    end
  endtask
  
  // 边界条件测试
  task corner_test;
    begin
      $display("=== 开始边界条件测试 ===");
      
      // 测试长脉冲和快速变化
      for (i = 0; i < 10; i = i + 1) begin
        a = i % 2; b = (i + 1) % 2; #10;
        if ((a ^ b) !== sum) begin
          $display("FAIL: Corner test case %d: a=%b, b=%b, expected sum=%b, got sum=%b", 
                   i, a, b, (a ^ b), sum);
          fail_count = fail_count + 1;
        end else begin
          $display("PASS: Corner test case %d: a=%b, b=%b, sum=%b", i, a, b, sum);
          pass_count = pass_count + 1;
        end
      end
      
      // 测试连续变化
      a = 0; b = 0; #10;
      a = 1; b = 1; #10;
      a = 0; b = 1; #10;
      a = 1; b = 0; #10;
      
      $display("=== 边界条件测试结束 ===");
    end
  endtask
  
  // 主测试流程
  initial begin
    // 初始化
    clk = 0;
    a = 0;
    b = 0;
    pass_count = 0;
    fail_count = 0;
    
    // 等待稳定
    #100;
    
    // 执行测试用例
    basic_test();
    corner_test();
    
    // 显示测试结果
    $display("=== 测试报告 ===");
    $display("通过测试用例数: %d", pass_count);
    $display("失败测试用例数: %d", fail_count);
    $display("总测试用例数: %d", pass_count + fail_count);
    
    if (fail_count == 0) begin
      $display("测试结果: 全部通过!");
    end else begin
      $display("测试结果: 存在失败!");
    end
    
    // 结束仿真
    #1000;
    $finish;
  end
  
endmodule