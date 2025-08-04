`timescale 1ns/1ps

module tb_simple_adder;

    // 信号声明
    reg  [7:0] a;
    reg  [7:0] b;
    wire [8:0] sum;
    
    // 时钟和复位信号
    reg clk;
    reg rst_n;
    
    // 测试控制信号
    integer i;
    integer test_case;
    integer error_count;
    
    // 实例化被测模块
    simple_adder uut (
        .a(a),
        .b(b),
        .sum(sum)
    );
    
    // 时钟生成
    always #5.0 clk = ~clk;
    
    // 复位生成
    initial begin
        clk = 0;
        rst_n = 0;
        a = 8'b0;
        b = 8'b0;
        
        // 复位持续时间
        #20 rst_n = 1;
    end
    
    // 测试激励生成 - basic_test
    initial begin
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, tb_simple_adder);
        
        error_count = 0;
        test_case = 0;
        
        $display("开始基本功能测试 (basic_test)");
        $display("时间\t\tA\t\tB\t\tSum\t\t期望值\t\t结果");
        
        // 基本功能测试
        for (i = 0; i < 100; i = i + 1) begin
            a = $random % 256;
            b = $random % 256;
            
            #10;
            
            if ((a + b) == sum) begin
                $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t通过", 
                         $time, a, b, sum, (a+b));
            end else begin
                $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t失败", 
                         $time, a, b, sum, (a+b));
                error_count = error_count + 1;
            end
        end
        
        test_case = 1;
        $display("基本功能测试完成，错误计数: %0d", error_count);
        
        // 边界条件测试
        $display("开始边界条件测试 (corner_test)");
        $display("时间\t\tA\t\tB\t\tSum\t\t期望值\t\t结果");
        
        // 测试最大值情况
        a = 8'hFF;
        b = 8'h00;
        #10;
        if ((a + b) == sum) begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t通过", 
                     $time, a, b, sum, (a+b));
        end else begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t失败", 
                     $time, a, b, sum, (a+b));
            error_count = error_count + 1;
        end
        
        a = 8'h00;
        b = 8'hFF;
        #10;
        if ((a + b) == sum) begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t通过", 
                     $time, a, b, sum, (a+b));
        end else begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t失败", 
                     $time, a, b, sum, (a+b));
            error_count = error_count + 1;
        end
        
        a = 8'hFF;
        b = 8'hFF;
        #10;
        if ((a + b) == sum) begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t通过", 
                     $time, a, b, sum, (a+b));
        end else begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t失败", 
                     $time, a, b, sum, (a+b));
            error_count = error_count + 1;
        end
        
        // 测试零值情况
        a = 8'h00;
        b = 8'h00;
        #10;
        if ((a + b) == sum) begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t通过", 
                     $time, a, b, sum, (a+b));
        end else begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t失败", 
                     $time, a, b, sum, (a+b));
            error_count = error_count + 1;
        end
        
        // 测试进位情况
        a = 8'h80;
        b = 8'h80;
        #10;
        if ((a + b) == sum) begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t通过", 
                     $time, a, b, sum, (a+b));
        end else begin
            $display("%0t\t%0d\t\t%0d\t\t%0d\t\t%0d\t\t失败", 
                     $time, a, b, sum, (a+b));
            error_count = error_count + 1;
        end
        
        $display("边界条件测试完成，错误计数: %0d", error_count);
        
        // 综合测试报告
        if (error_count == 0) begin
            $display("测试通过！所有测试用例均通过。");
        end else begin
            $display("测试失败！发现 %0d 个错误。", error_count);
        end
        
        $finish;
    end
    
    // 监控信号变化
    initial begin
        $monitor("监控: 时间=%0t, A=%0d, B=%0d, Sum=%0d", 
                 $time, a, b, sum);
    end

endmodule