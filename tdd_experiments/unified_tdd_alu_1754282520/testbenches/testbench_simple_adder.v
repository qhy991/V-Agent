`timescale 1ns/1ps

module tb_simple_adder;

    // 信号声明
    reg  [7:0] a;
    reg  [7:0] b;
    wire [8:0] sum;
    
    // 时钟信号
    reg clk;
    
    // 测试控制信号
    reg test_done;
    
    // 实例化被测模块
    simple_adder uut (
        .a(a),
        .b(b),
        .sum(sum)
    );
    
    // 时钟生成
    always #5 clk = ~clk;
    
    // 测试激励和验证
    initial begin
        // 初始化信号
        a = 8'b0;
        b = 8'b0;
        clk = 1'b0;
        test_done = 1'b0;
        
        // 开始仿真
        $display("开始简单加法器测试");
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, tb_simple_adder);
        
        // 基本功能测试
        $display("执行基本功能测试...");
        basic_functionality();
        
        // 边界条件测试
        $display("执行边界条件测试...");
        boundary_conditions();
        
        // 测试完成
        test_done = 1'b1;
        $display("所有测试完成");
        $finish;
    end
    
    // 基本功能测试
    task basic_functionality;
        integer i;
        integer error_count;
        error_count = 0;
        
        for (i = 0; i < 100; i = i + 1) begin
            a = $random % 256;
            b = $random % 256;
            #10;
            
            if (sum !== (a + b)) begin
                $display("错误: a=%d, b=%d, 期望=%d, 实际=%d", a, b, (a+b), sum);
                error_count = error_count + 1;
            end else begin
                $display("通过: a=%d, b=%d, sum=%d", a, b, sum);
            end
        end
        
        if (error_count == 0) begin
            $display("基本功能测试通过 - 无错误");
        end else begin
            $display("基本功能测试失败 - 发现 %d 个错误", error_count);
        end
    endtask
    
    // 边界条件测试
    task boundary_conditions;
        integer i;
        integer error_count;
        error_count = 0;
        
        // 测试零值情况
        a = 8'b0;
        b = 8'b0;
        #10;
        if (sum !== 9'b0) begin
            $display("错误: 零值测试失败 - 期望=0, 实际=%d", sum);
            error_count = error_count + 1;
        end else begin
            $display("通过: 零值测试");
        end
        
        // 测试最大值情况
        a = 8'hFF;
        b = 8'hFF;
        #10;
        if (sum !== 9'h1FE) begin
            $display("错误: 最大值测试失败 - 期望=510, 实际=%d", sum);
            error_count = error_count + 1;
        end else begin
            $display("通过: 最大值测试");
        end
        
        // 测试溢出情况
        a = 8'hFF;
        b = 8'h01;
        #10;
        if (sum !== 9'h100) begin
            $display("错误: 溢出测试失败 - 期望=256, 实际=%d", sum);
            error_count = error_count + 1;
        end else begin
            $display("通过: 溢出测试");
        end
        
        // 测试中间值
        a = 8'h80;
        b = 8'h80;
        #10;
        if (sum !== 9'h100) begin
            $display("错误: 中间值测试失败 - 期望=256, 实际=%d", sum);
            error_count = error_count + 1;
        end else begin
            $display("通过: 中间值测试");
        end
        
        // 测试随机边界值
        for (i = 0; i < 20; i = i + 1) begin
            a = $random % 256;
            b = $random % 256;
            #10;
            
            if (sum !== (a + b)) begin
                $display("错误: 边界随机测试失败 - a=%d, b=%d, 期望=%d, 实际=%d", 
                         a, b, (a+b), sum);
                error_count = error_count + 1;
            end else begin
                $display("通过: 边界随机测试 - a=%d, b=%d, sum=%d", a, b, sum);
            end
        end
        
        if (error_count == 0) begin
            $display("边界条件测试通过 - 无错误");
        end else begin
            $display("边界条件测试失败 - 发现 %d 个错误", error_count);
        end
    endtask
    
    // 监控信号变化
    initial begin
        $monitor("时间 %0t: a=%0d, b=%0d, sum=%0d", $time, a, b, sum);
    end

endmodule