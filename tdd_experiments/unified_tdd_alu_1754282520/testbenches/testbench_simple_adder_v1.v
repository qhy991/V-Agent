`timescale 1ns/1ps

module tb_simple_adder;

    // 信号声明
    reg  [7:0] a;
    reg  [7:0] b;
    wire [8:0] sum;
    
    // 时钟信号
    reg clk;
    
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
    
    // 测试激励和验证
    initial begin
        // 初始化
        clk = 0;
        a = 8'b0;
        b = 8'b0;
        error_count = 0;
        
        // 开始波形记录
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, tb_simple_adder);
        
        // 显示测试开始信息
        $display("===================================");
        $display("Simple Adder Testbench Started");
        $display("===================================");
        
        // 基本功能测试
        $display("Testing Basic Functionality...");
        test_case = 1;
        for (i = 0; i < 100; i = i + 1) begin
            a = $random % 256;
            b = $random % 256;
            #10;
            if (sum !== (a + b)) begin
                $display("ERROR: Basic functionality test failed at cycle %0d", i);
                $display("  a = %b, b = %b, expected = %b, actual = %b", 
                         a, b, (a + b), sum);
                error_count = error_count + 1;
            end
        end
        
        // 边界条件测试
        $display("Testing Boundary Conditions...");
        test_case = 2;
        
        // 测试零值情况
        a = 8'b0;
        b = 8'b0;
        #10;
        if (sum !== 9'b0) begin
            $display("ERROR: Zero values test failed");
            error_count = error_count + 1;
        end
        
        a = 8'b0;
        b = 8'd255;
        #10;
        if (sum !== 9'd255) begin
            $display("ERROR: Zero + max value test failed");
            error_count = error_count + 1;
        end
        
        a = 8'd255;
        b = 8'b0;
        #10;
        if (sum !== 9'd255) begin
            $display("ERROR: Max value + zero test failed");
            error_count = error_count + 1;
        end
        
        // 测试最大值加最大值
        a = 8'd255;
        b = 8'd255;
        #10;
        if (sum !== 9'd510) begin
            $display("ERROR: Max value + max value test failed");
            error_count = error_count + 1;
        end
        
        // 测试进位情况
        a = 8'd255;
        b = 8'd1;
        #10;
        if (sum !== 9'd256) begin
            $display("ERROR: Carry case test failed");
            error_count = error_count + 1;
        end
        
        // 测试随机边界值
        for (i = 0; i < 50; i = i + 1) begin
            a = $random % 256;
            b = 8'd255 - (a[7] ? 8'd1 : 8'd0);  // 确保产生进位
            #10;
            if (sum !== (a + b)) begin
                $display("ERROR: Boundary random test failed at cycle %0d", i);
                error_count = error_count + 1;
            end
        end
        
        // 显示测试结果
        $display("===================================");
        if (error_count == 0) begin
            $display("TEST RESULT: PASSED - All tests passed");
        end else begin
            $display("TEST RESULT: FAILED - %0d errors found", error_count);
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