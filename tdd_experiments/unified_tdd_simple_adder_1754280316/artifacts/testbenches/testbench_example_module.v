`timescale 1ns/1ps

module example_module_tb;

    // 信号声明
    reg clk;
    reg rst_n;
    reg [7:0] data_in;
    wire [7:0] data_out;

    // 仿真时间控制
    integer i;
    integer cycle_count;

    // VCD波形文件
    initial begin
        $dumpfile("example_module.vcd");
        $dumpvars(0, example_module_tb);
    end

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // 复位信号生成
    initial begin
        rst_n = 0;
        #10 rst_n = 1;
    end

    // 实例化被测模块
    example_module uut (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(data_in),
        .data_out(data_out)
    );

    // 测试场景1: basic_functionality
    initial begin
        $display("=== 开始基本功能测试 ===");
        
        // 初始化
        data_in = 8'h00;
        cycle_count = 0;
        
        // 等待复位完成
        repeat(2) @(posedge clk);
        
        // 测试数据输入序列
        for(i = 0; i < 10; i = i + 1) begin
            data_in = i;
            @(posedge clk);
            $display("Cycle %0d: data_in = %h, data_out = %h", cycle_count, data_in, data_out);
            cycle_count = cycle_count + 1;
        end
        
        // 测试边界值
        data_in = 8'hFF;
        @(posedge clk);
        $display("Cycle %0d: data_in = %h, data_out = %h", cycle_count, data_in, data_out);
        cycle_count = cycle_count + 1;
        
        data_in = 8'h00;
        @(posedge clk);
        $display("Cycle %0d: data_in = %h, data_out = %h", cycle_count, data_in, data_out);
        cycle_count = cycle_count + 1;
        
        $display("=== 基本功能测试完成 ===");
    end

    // 测试场景2: reset_behavior
    initial begin
        $display("=== 开始复位行为测试 ===");
        
        // 产生复位信号
        rst_n = 0;
        @(posedge clk);
        $display("复位期间: data_in = %h, data_out = %h", data_in, data_out);
        
        // 等待一段时间后释放复位
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
        $display("复位释放后: data_in = %h, data_out = %h", data_in, data_out);
        
        // 再次测试数据传输
        data_in = 8'hAA;
        @(posedge clk);
        $display("复位后测试: data_in = %h, data_out = %h", data_in, data_out);
        
        $display("=== 复位行为测试完成 ===");
    end

    // 监控信号变化
    initial begin
        $monitor("监控: time=%0t, clk=%b, rst_n=%b, data_in=%h, data_out=%h", 
                 $time, clk, rst_n, data_in, data_out);
    end

    // 仿真结束控制
    initial begin
        // 等待足够多的时钟周期
        repeat(1000) @(posedge clk);
        
        // 检查是否达到预期仿真时间
        if(cycle_count >= 1000) begin
            $display("=== 仿真完成，达到最大时钟周期数 ===");
        end else begin
            $display("=== 仿真完成，测试执行完毕 ===");
        end
        
        $finish;
    end

endmodule