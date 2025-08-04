`timescale 1ns/1ps

module tb_simple_adder;

  // 信号声明
  reg clk;
  reg a;
  reg b;
  wire sum;
  
  // 用于计数的变量
  integer i;
  
  // 实例化被测模块
  simple_adder uut (
    .a(a),
    .b(b),
    .sum(sum)
  );
  
  // 时钟生成
  always #5 clk = ~clk;
  
  // 测试场景：basic_test - 基本功能验证
  task basic_test;
    begin
      $display("=== 开始基本功能测试 ===");
      
      // 测试所有可能的输入组合
      a = 0; b = 0; #10;
      if (sum !== (a ^ b)) 
        $display("错误: a=%b, b=%b, sum=%b, 期望值=%b", a, b, sum, (a ^ b));
      else
        $display("正确: a=%b, b=%b, sum=%b", a, b, sum);
        
      a = 0; b = 1; #10;
      if (sum !== (a ^ b)) 
        $display("错误: a=%b, b=%b, sum=%b, 期望值=%b", a, b, sum, (a ^ b));
      else
        $display("正确: a=%b, b=%b, sum=%b", a, b, sum);
        
      a = 1; b = 0; #10;
      if (sum !== (a ^ b)) 
        $display("错误: a=%b, b=%b, sum=%b, 期望值=%b", a, b, sum, (a ^ b));
      else
        $display("正确: a=%b, b=%b, sum=%b", a, b, sum);
        
      a = 1; b = 1; #10;
      if (sum !== (a ^ b)) 
        $display("错误: a=%b, b=%b, sum=%b, 期望值=%b", a, b, sum, (a ^ b));
      else
        $display("正确: a=%b, b=%b, sum=%b", a, b, sum);
        
      $display("=== 基本功能测试完成 ===");
    end
  endtask
  
  // 测试场景：corner_test - 边界条件测试
  task corner_test;
    begin
      $display("=== 开始边界条件测试 ===");
      
      // 测试长脉冲和快速变化
      for (i = 0; i < 10; i = i + 1) begin
        a = i % 2;
        b = (i + 1) % 2;
        #10;
        if (sum !== (a ^ b)) 
          $display("错误: 边界测试失败, a=%b, b=%b, sum=%b, 期望值=%b", a, b, sum, (a ^ b));
        else
          $display("正确: 边界测试, a=%b, b=%b, sum=%b", a, b, sum);
      end
      
      // 测试连续变化
      a = 0; b = 0; #10;
      a = 1; b = 1; #10;
      a = 0; b = 1; #10;
      a = 1; b = 0; #10;
      
      $display("=== 边界条件测试完成 ===");
    end
  endtask
  
  // 监控信号
  initial begin
    $monitor("时间=%0t: a=%b, b=%b, sum=%b", $time, a, b, sum);
  end
  
  // 主测试流程
  initial begin
    // 初始化
    clk = 0;
    a = 0;
    b = 0;
    
    // 设置波形转储
    $dumpfile("simple_adder.vcd");
    $dumpvars(0, tb_simple_adder);
    
    // 执行测试
    basic_test();
    corner_test();
    
    // 仿真结束
    $display("=== 所有测试完成 ===");
    $finish;
  end
  
  // 仿真时间控制
  initial begin
    #100000 $display("仿真时间超限，强制结束");
    $finish;
  end

endmodule