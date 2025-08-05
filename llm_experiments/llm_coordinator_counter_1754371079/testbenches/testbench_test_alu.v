`timescale 1ns/1ps

module test_alu_tb;

    // 信号声明
    reg [7:0] a;
    reg [7:0] b;
    wire [7:0] result;
    
    // 时钟信号
    reg clk;
    reg rst_n;
    
    // 测试控制信号
    integer test_case_num;
    integer error_count;
    integer test_count;
    
    // 时钟生成
    always begin
        #5.0 clk = ~clk;
    end
    
    // 被测模块实例化
    test_alu u_test_alu (
        .a(a),
        .b(b),
        .result(result)
    );
    
    // 初始化
    initial begin
        // 信号初始化
        clk = 0;
        rst_n = 0;
        a = 0;
        b = 0;
        
        test_case_num = 0;
        error_count = 0;
        test_count = 0;
        
        // 复位序列
        #20 rst_n = 1;
        
        // 波形转储设置
        $dumpfile("test_alu_tb.vcd");
        $dumpvars(0, test_alu_tb);
        
        $display("================================================");
        $display("Starting test_alu Testbench");
        $display("================================================");
        $display("Time\t\tTest Case\tA\tB\tExpected\tActual\tStatus");
        $display("------------------------------------------------");
        
        // basic_test: 基本功能测试
        basic_test();
        
        // 等待一段时间确保所有操作完成
        #100;
        
        // 测试总结
        $display("================================================");
        $display("Test Summary:");
        $display("Total test cases executed: %0d", test_count);
        $display("Errors found: %0d", error_count);
        if (error_count == 0) begin
            $display("RESULT: ALL TESTS PASSED");
        end else begin
            $display("RESULT: TESTS FAILED");
        end
        $display("================================================");
        
        // 结束仿真
        $finish;
    end
    
    // 监视器
    initial begin
        $monitor("At time %t: a=0x%02h, b=0x%02h, result=0x%02h", $time, a, b, result);
    end
    
    // basic_test任务
    task basic_test;
    begin
        test_case_num = test_case_num + 1;
        $display("");
        $display("--- Basic Functionality Test ---");
        
        // 测试用例1: 零值相加
        test_count = test_count + 1;
        a = 8'h00;
        b = 8'h00;
        #10;
        check_result(8'h00);
        
        // 测试用例2: 小数值相加
        test_count = test_count + 1;
        a = 8'h05;
        b = 8'h03;
        #10;
        check_result(8'h08);
        
        // 测试用例3: 中等数值相加
        test_count = test_count + 1;
        a = 8'h10;
        b = 8'h20;
        #10;
        check_result(8'h30);
        
        // 测试用例4: 较大数值相加
        test_count = test_count + 1;
        a = 8'h50;
        b = 8'h30;
        #10;
        check_result(8'h80);
        
        // 测试用例5: 最大值范围测试
        test_count = test_count + 1;
        a = 8'hFF;
        b = 8'h00;
        #10;
        check_result(8'hFF);
        
        // 测试用例6: 溢出测试（虽然模块不处理溢出，但验证基本加法）
        test_count = test_count + 1;
        a = 8'h80;
        b = 8'h80;
        #10;
        check_result(8'h00); // 0x80 + 0x80 = 0x100, 8位结果为0x00
        
        // 测试用例7: 随机值测试1
        test_count = test_count + 1;
        a = 8'hA5;
        b = 8'h3C;
        #10;
        check_result(8'hE1);
        
        // 测试用例8: 随机值测试2
        test_count = test_count + 1;
        a = 8'h7F;
        b = 8'h01;
        #10;
        check_result(8'h80);
        
        // 测试用例9: 随机值测试3
        test_count = test_count + 1;
        a = 8'hC3;
        b = 8'h2D;
        #10;
        check_result(8'hF0);
        
        // 测试用例10: 边界值测试
        test_count = test_count + 1;
        a = 8'hFE;
        b = 8'h01;
        #10;
        check_result(8'hFF);
        
        $display("--- Basic Functionality Test Completed ---");
        $display("");
    end
    endtask
    
    // 结果检查任务
    task check_result;
        input [7:0] expected;
    begin
        if (result !== expected) begin
            error_count = error_count + 1;
            $display("%0t\t\tTC%0d\t\t0x%02h\t0x%02h\t0x%02h\t\t0x%02h\tFAIL", 
                     $time, test_count, a, b, expected, result);
        end else begin
            $display("%0t\t\tTC%0d\t\t0x%02h\t0x%02h\t0x%02h\t\t0x%02h\tPASS", 
                     $time, test_count, a, b, expected, result);
        end
    end
    endtask
    
    // 仿真时间控制
    initial begin
        // 等待10000个时钟周期
        repeat(10000) begin
            @(posedge clk);
        end
        $display("Reached 10000 clock cycles. Ending simulation.");
        $finish;
    end

endmodule