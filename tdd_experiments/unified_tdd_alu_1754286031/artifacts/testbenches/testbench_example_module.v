`timescale 1ns/1ps

module example_module_tb;

// 信号声明
reg clk;
reg rst_n;
reg [7:0] data_in;
wire [7:0] data_out;

// 时钟生成
initial begin
    clk = 0;
    forever #5 clk = ~clk;  // 10ns周期时钟
end

// 测试激励
initial begin
    // 初始化信号
    rst_n = 1;
    data_in = 8'h0;
    
    // 等待稳定
    #10;
    
    // 执行基本功能测试
    $display("开始基本功能测试...");
    basic_functionality();
    
    // 执行复位测试
    $display("开始复位功能测试...");
    reset_test();
    
    // 结束仿真
    $display("测试完成，结束仿真");
    $finish;
end

// 基本功能测试
task basic_functionality;
    integer i;
    
    // 测试数据输入序列
    for (i = 0; i < 10; i = i + 1) begin
        data_in = i;
        #10;
        $display("时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
    end
    
    // 测试更多数据
    for (i = 10; i < 20; i = i + 1) begin
        data_in = i;
        #10;
        $display("时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
    end
    
    // 测试边界值
    data_in = 8'hFF;
    #10;
    $display("时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
    
    data_in = 8'h00;
    #10;
    $display("时钟周期 %0d: 输入 = %h, 输出 = %h", i+1, data_in, data_out);
endtask

// 复位功能测试
task reset_test;
    integer i;
    
    // 测试正常运行
    $display("测试正常运行状态");
    for (i = 0; i < 5; i = i + 1) begin
        data_in = i;
        #10;
        $display("正常运行 - 时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
    end
    
    // 产生复位信号
    $display("产生复位信号");
    rst_n = 0;
    #10;
    $display("复位期间 - 时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
    
    // 检查复位后输出是否为0
    if (data_out !== 8'h0) begin
        $display("错误：复位后输出不为0，实际值 = %h", data_out);
    end else begin
        $display("正确：复位后输出为0");
    end
    
    // 恢复复位信号
    rst_n = 1;
    #10;
    $display("复位恢复后 - 时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
    
    // 测试复位后数据是否正确传递
    data_in = 8'hAA;
    #10;
    $display("复位后数据传递 - 时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
    
    // 再次测试复位
    rst_n = 0;
    #10;
    $display("再次复位 - 时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
    
    rst_n = 1;
    #10;
    $display("再次复位恢复 - 时钟周期 %0d: 输入 = %h, 输出 = %h", i, data_in, data_out);
endtask

// 实例化被测模块
example_module uut (
    .clk(clk),
    .rst_n(rst_n),
    .data_in(data_in),
    .data_out(data_out)
);

// 监控信号变化
initial begin
    $monitor("监控: 时间=%0t, 时钟=%b, 复位=%b, 输入=%h, 输出=%h", 
             $time, clk, rst_n, data_in, data_out);
end

// 波形转储设置
initial begin
    $dumpfile("example_module.vcd");
    $dumpvars(0, example_module_tb);
end

endmodule