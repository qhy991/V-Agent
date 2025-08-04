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
        
        // 初始化复位
        #10 rst_n = 1;
        
        // 测试开始
        $display("=== Simple Adder Testbench Started ===");
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, tb_simple_adder);
        
        // 初始化错误计数器
        error_count = 0;
        
        // 运行基本测试
        test_case = 0;
        basic_test();
        
        // 运行边界测试
        test_case = 1;
        corner_test();
        
        // 测试结束
        $display("=== Testbench Completed ===");
        $display("Total Errors: %d", error_count);
        
        if (error_count == 0) begin
            $display("RESULT: All tests passed!");
        end else begin
            $display("RESULT: Some tests failed!");
        end
        
        $finish;
    end
    
    // 基本功能测试
    task basic_test;
        integer j;
        begin
            $display("Starting Basic Functionality Test...");
            
            for (j = 0; j < 256; j = j + 1) begin
                a = j;
                b = j;
                #10;
                
                if (sum !== (a + b)) begin
                    $display("ERROR: Basic test failed at a=%d, b=%d, expected=%d, actual=%d", 
                             a, b, (a + b), sum);
                    error_count = error_count + 1;
                end
            end
            
            $display("Basic Functionality Test Completed.");
        end
    endtask
    
    // 边界条件测试
    task corner_test;
        integer k;
        begin
            $display("Starting Corner Cases Test...");
            
            // 测试零值情况
            a = 8'h00;
            b = 8'h00;
            #10;
            if (sum !== 9'h000) begin
                $display("ERROR: Zero case failed, expected=0, actual=%d", sum);
                error_count = error_count + 1;
            end
            
            a = 8'h00;
            b = 8'hFF;
            #10;
            if (sum !== 9'h0FF) begin
                $display("ERROR: Zero and max case failed, expected=255, actual=%d", sum);
                error_count = error_count + 1;
            end
            
            a = 8'hFF;
            b = 8'h00;
            #10;
            if (sum !== 9'h0FF) begin
                $display("ERROR: Max and zero case failed, expected=255, actual=%d", sum);
                error_count = error_count + 1;
            end
            
            a = 8'hFF;
            b = 8'hFF;
            #10;
            if (sum !== 9'h1FE) begin
                $display("ERROR: Max values case failed, expected=510, actual=%d", sum);
                error_count = error_count + 1;
            end
            
            // 测试中间值
            for (k = 0; k < 10; k = k + 1) begin
                a = 8'h80;
                b = 8'h80;
                #10;
                if (sum !== 9'h100) begin
                    $display("ERROR: Middle value case failed, expected=256, actual=%d", sum);
                    error_count = error_count + 1;
                end
            end
            
            $display("Corner Cases Test Completed.");
        end
    endtask
    
    // 监控信号变化
    initial begin
        $monitor("Time=%0t: a=%h, b=%h, sum=%h", $time, a, b, sum);
    end

endmodule