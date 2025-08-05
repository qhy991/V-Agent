`timescale 1ns/1ps

module alu_8bit_tb;

    // 信号声明
    reg [7:0] a;
    reg [7:0] b;
    reg [1:0] op;
    wire [7:0] result;
    wire zero;
    
    // 测试计数器
    integer passed_count;
    integer failed_count;
    integer total_count;
    integer test_number;
    
    // 时钟信号
    reg clk;
    
    // 被测模块实例化
    alu_8bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    // 时钟生成
    always begin
        #5 clk = ~clk;
    end
    
    // 初始化
    initial begin
        // 初始化信号
        clk = 0;
        a = 0;
        b = 0;
        op = 0;
        
        // 初始化计数器
        passed_count = 0;
        failed_count = 0;
        total_count = 0;
        test_number = 0;
        
        // 波形转储
        $dumpfile("alu_8bit_tb.vcd");
        $dumpvars(0, alu_8bit_tb);
        
        // 等待一段时间让信号稳定
        #20;
        
        // ==================== 加法测试 ====================
        $display("Starting addition_tests...");
        
        // 测试用例 1: 简单加法
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h10;
        b = 8'h20;
        op = 2'b00;
        #10;
        if (result === 8'h30) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - addition_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'h30, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - addition_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h30, result);
        end
        
        // 测试用例 2: 带进位的加法
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'hFF;
        b = 8'h01;
        op = 2'b00;
        #10;
        if (result === 8'h00) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - addition_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'h00, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - addition_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h00, result);
        end
        
        // 测试用例 3: 零加法
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h00;
        b = 8'h00;
        op = 2'b00;
        #10;
        if (result === 8'h00) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - addition_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'h00, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - addition_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h00, result);
        end
        
        // ==================== 减法测试 ====================
        $display("Starting subtraction_tests...");
        
        // 测试用例 4: 简单减法
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h30;
        b = 8'h10;
        op = 2'b01;
        #10;
        if (result === 8'h20) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - subtraction_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'h20, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - subtraction_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h20, result);
        end
        
        // 测试用例 5: 结果为负数的减法
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h10;
        b = 8'h30;
        op = 2'b01;
        #10;
        if (result === 8'hE0) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - subtraction_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'hE0, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - subtraction_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'hE0, result);
        end
        
        // 测试用例 6: 零减法
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h00;
        b = 8'h00;
        op = 2'b01;
        #10;
        if (result === 8'h00) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - subtraction_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'h00, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - subtraction_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h00, result);
        end
        
        // ==================== 与运算测试 ====================
        $display("Starting and_tests...");
        
        // 测试用例 7: 简单与运算
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'hFF;
        b = 8'h0F;
        op = 2'b10;
        #10;
        if (result === 8'h0F) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - and_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'h0F, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - and_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h0F, result);
        end
        
        // 测试用例 8: 零与运算
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'hFF;
        b = 8'h00;
        op = 2'b10;
        #10;
        if (result === 8'h00) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - and_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'h00, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - and_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h00, result);
        end
        
        // 测试用例 9: 全与运算
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'hFF;
        b = 8'hFF;
        op = 2'b10;
        #10;
        if (result === 8'hFF) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - and_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'hFF, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - and_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'hFF, result);
        end
        
        // ==================== 或运算测试 ====================
        $display("Starting or_tests...");
        
        // 测试用例 10: 简单或运算
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'hF0;
        b = 8'h0F;
        op = 2'b11;
        #10;
        if (result === 8'hFF) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - or_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'hFF, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - or_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'hFF, result);
        end
        
        // 测试用例 11: 零或运算
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h00;
        b = 8'h00;
        op = 2'b11;
        #10;
        if (result === 8'h00) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - or_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'h00, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - or_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'h00, result);
        end
        
        // 测试用例 12: 全或运算
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h0F;
        b = 8'hF0;
        op = 2'b11;
        #10;
        if (result === 8'hFF) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - or_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", 8'hFF, result);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - or_tests", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", 8'hFF, result);
        end
        
        // ==================== 零标志位测试 ====================
        $display("Starting zero_flag_tests...");
        
        // 测试用例 13: 加法结果为零
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h00;
        b = 8'h00;
        op = 2'b00;
        #10;
        if (zero === 1'b1) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - zero_flag_tests", $time, test_number);
            $display("Expected: %b, Got: %b, Status: PASS", 1'b1, zero);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - zero_flag_tests", $time, test_number);
            $display("Expected: %b, Got: %b, Status: FAIL", 1'b1, zero);
        end
        
        // 测试用例 14: 减法结果为零
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h55;
        b = 8'h55;
        op = 2'b01;
        #10;
        if (zero === 1'b1) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - zero_flag_tests", $time, test_number);
            $display("Expected: %b, Got: %b, Status: PASS", 1'b1, zero);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - zero_flag_tests", $time, test_number);
            $display("Expected: %b, Got: %b, Status: FAIL", 1'b1, zero);
        end
        
        // 测试用例 15: 与运算结果为零
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'hF0;
        b = 8'h0F;
        op = 2'b10;
        #10;
        if (zero === 1'b1) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - zero_flag_tests", $time, test_number);
            $display("Expected: %b, Got: %b, Status: PASS", 1'b1, zero);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - zero_flag_tests", $time, test_number);
            $display("Expected: %b, Got: %b, Status: FAIL", 1'b1, zero);
        end
        
        // 测试用例 16: 或运算结果非零
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = 8'h00;
        b = 8'h01;
        op = 2'b11;
        #10;
        if (zero === 1'b0) begin
            passed_count = passed_count + 1;
            $display("Time=%0t: Test Case %0d - zero_flag_tests", $time, test_number);
            $display("Expected: %b, Got: %b, Status: PASS", 1'b0, zero);
        end else begin
            failed_count = failed_count + 1;
            $display("Time=%0t: Test Case %0d - zero_flag_tests", $time, test_number);
            $display("Expected: %b, Got: %b, Status: FAIL", 1'b0, zero);
        end
        
        // 等待一些额外时间以确保所有信号稳定
        #100;
        
        // 输出测试统计信息
        $display("==================================================");
        $display("Test Summary:");
        $display("Total Tests: %0d", total_count);
        $display("Passed: %0d", passed_count);
        $display("Failed: %0d", failed_count);
        $display("==================================================");
        if (failed_count == 0) begin
            $display("All passed!");
        end
        $display("==================================================");
        
        // 结束仿真
        $finish;
    end

endmodule