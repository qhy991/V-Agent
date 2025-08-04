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
  always begin
    #5.0 clk = ~clk;
  end
  
  // 测试激励和结果检查
  initial begin
    // 初始化信号
    a = 0;
    b = 0;
    clk = 0;
    
    // 打开波形文件
    $dumpfile("simple_adder.vcd");
    $dumpvars(0, tb_simple_adder);
    
    // 显示测试开始信息
    $display("=== Simple Adder Testbench Started ===");
    $display("Time\tA\tB\tSum");
    
    // 基本功能验证测试
    $display("Testing Basic Functionality...");
    for (i = 0; i < 4; i = i + 1) begin
      case (i)
        0: begin a = 0; b = 0; end
        1: begin a = 0; b = 1; end
        2: begin a = 1; b = 0; end
        3: begin a = 1; b = 1; end
      endcase
      
      #10;
      
      // 检查结果
      if ((a ^ b) !== sum) begin
        $display("ERROR: Basic functionality test failed at time %0t", $time);
        $display("Expected: %b, Actual: %b", (a ^ b), sum);
      end else begin
        $display("%0t\t%b\t%b\t%b", $time, a, b, sum);
      end
    end
    
    // 边界条件测试
    $display("Testing Boundary Conditions...");
    for (i = 0; i < 100; i = i + 1) begin
      a = $random % 2;
      b = $random % 2;
      #10;
      
      // 检查结果
      if ((a ^ b) !== sum) begin
        $display("ERROR: Boundary condition test failed at time %0t", $time);
        $display("Expected: %b, Actual: %b", (a ^ b), sum);
      end else begin
        $display("%0t\t%b\t%b\t%b", $time, a, b, sum);
      end
    end
    
    // 长时间运行测试
    $display("Running extended test for 10000 clock cycles...");
    for (i = 0; i < 10000; i = i + 1) begin
      a = $random % 2;
      b = $random % 2;
      #10;
      
      // 检查结果
      if ((a ^ b) !== sum) begin
        $display("ERROR: Extended test failed at time %0t", $time);
        $display("Expected: %b, Actual: %b", (a ^ b), sum);
      end
    end
    
    // 显示测试结束信息
    $display("=== Simple Adder Testbench Completed ===");
    
    // 结束仿真
    $finish;
  end
  
  // 监控信号变化
  initial begin
    $monitor("Monitor: Time=%0t A=%b B=%b Sum=%b", $time, a, b, sum);
  end

endmodule