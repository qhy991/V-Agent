`timescale 1ns/1ps

module tb_simple_adder;
  reg a, b;
  wire sum;
  
  // 实例化被测模块
  simple_adder uut (.a(a), .b(b), .sum(sum));
  
  // 测试向量
  initial begin
    $display("开始测试 simple_adder 模块");
    
    // 测试所有可能的输入组合
    a = 0; b = 0; #10;
    $display("a=%b, b=%b, sum=%b", a, b, sum);
    
    a = 0; b = 1; #10;
    $display("a=%b, b=%b, sum=%b", a, b, sum);
    
    a = 1; b = 0; #10;
    $display("a=%b, b=%b, sum=%b", a, b, sum);
    
    a = 1; b = 1; #10;
    $display("a=%b, b=%b, sum=%b", a, b, sum);
    
    $display("测试完成");
    $finish;
  end
endmodule