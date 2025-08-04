`timescale 1ns/1ps

module tb_alu_32bit;

    // 信号声明
    reg [31:0] a;
    reg [31:0] b;
    reg [3:0] op;
    wire [31:0] result;
    wire [0:0] zero;
    
    // 时钟和复位信号
    reg clk;
    reg rst_n;
    
    // 测试结果变量
    integer test_passed;
    integer test_failed;
    integer i;
    
    // 实例化被测模块
    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    // 时钟生成
    always #5 clk = ~clk;
    
    // 测试开始
    initial begin
        // 初始化信号
        clk = 0;
        rst_n = 0;
        a = 0;
        b = 0;
        op = 0;
        
        // 显示测试开始信息
        $display("===================================");
        $display("ALU 32BIT Testbench Started");
        $display("===================================");
        
        // 设置波形转储
        $dumpfile("alu_32bit.vcd");
        $dumpvars(0, tb_alu_32bit);
        
        // 复位序列
        #10 rst_n = 1;
        
        // 运行所有测试场景
        addition_test();
        subtraction_test();
        multiplication_test();
        division_test();
        logical_and_test();
        logical_or_test();
        logical_xor_test();
        shift_left_test();
        shift_right_test();
        zero_flag_test();
        boundary_test();
        
        // 显示测试报告
        $display("===================================");
        $display("Test Report:");
        $display("Passed Tests: %d", test_passed);
        $display("Failed Tests: %d", test_failed);
        $display("Total Tests: %d", test_passed + test_failed);
        $display("===================================");
        
        if (test_failed == 0) begin
            $display("All tests PASSED!");
        end else begin
            $display("Some tests FAILED!");
        end
        
        // 结束仿真
        #100 $finish;
    end
    
    // 监控信号变化
    initial begin
        $monitor("Time=%0t: a=0x%08h, b=0x%08h, op=%b, result=0x%08h, zero=%b",
                 $time, a, b, op, result, zero);
    end
    
    // 加法运算测试
    task addition_test;
        integer j;
        begin
            $display("Running Addition Test...");
            for (j = 0; j < 10; j = j + 1) begin
                a = j * 100;
                b = j * 50;
                op = 4'b0000;
                #10;
                if (result != (a + b)) begin
                    $display("Addition Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a + b), result);
                    test_failed = test_failed + 1;
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Addition Test Completed.");
        end
    endtask
    
    // 减法运算测试
    task subtraction_test;
        integer j;
        begin
            $display("Running Subtraction Test...");
            for (j = 0; j < 10; j = j + 1) begin
                a = j * 200;
                b = j * 75;
                op = 4'b0001;
                #10;
                if (result != (a - b)) begin
                    $display("Subtraction Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a - b), result);
                    test_failed = test_failed + 1;
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Subtraction Test Completed.");
        end
    endtask
    
    // 乘法运算测试
    task multiplication_test;
        integer j;
        begin
            $display("Running Multiplication Test...");
            for (j = 1; j <= 10; j = j + 1) begin
                a = j * 10;
                b = j * 5;
                op = 4'b0010;
                #10;
                if (result != (a * b)) begin
                    $display("Multiplication Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a * b), result);
                    test_failed = test_failed + 1;
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Multiplication Test Completed.");
        end
    endtask
    
    // 除法运算测试
    task division_test;
        integer j;
        begin
            $display("Running Division Test...");
            for (j = 1; j <= 10; j = j + 1) begin
                a = j * 100;
                b = j * 10;
                op = 4'b0011;
                #10;
                if ((b != 0) && (result != (a / b))) begin
                    $display("Division Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a / b), result);
                    test_failed = test_failed + 1;
                end else if (b == 0) begin
                    // 除零情况应该返回0
                    if (result != 0) begin
                        $display("Division by Zero Test Failed at cycle %0d: Expected 0x00000000, Got 0x%08h", 
                                 j, result);
                        test_failed = test_failed + 1;
                    end else begin
                        test_passed = test_passed + 1;
                    end
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Division Test Completed.");
        end
    endtask
    
    // 逻辑与运算测试
    task logical_and_test;
        integer j;
        begin
            $display("Running Logical AND Test...");
            for (j = 0; j < 10; j = j + 1) begin
                a = j * 100;
                b = j * 50;
                op = 4'b0100;
                #10;
                if (result != (a & b)) begin
                    $display("Logical AND Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a & b), result);
                    test_failed = test_failed + 1;
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Logical AND Test Completed.");
        end
    endtask
    
    // 逻辑或运算测试
    task logical_or_test;
        integer j;
        begin
            $display("Running Logical OR Test...");
            for (j = 0; j < 10; j = j + 1) begin
                a = j * 100;
                b = j * 50;
                op = 4'b0101;
                #10;
                if (result != (a | b)) begin
                    $display("Logical OR Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a | b), result);
                    test_failed = test_failed + 1;
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Logical OR Test Completed.");
        end
    endtask
    
    // 逻辑异或运算测试
    task logical_xor_test;
        integer j;
        begin
            $display("Running Logical XOR Test...");
            for (j = 0; j < 10; j = j + 1) begin
                a = j * 100;
                b = j * 50;
                op = 4'b0110;
                #10;
                if (result != (a ^ b)) begin
                    $display("Logical XOR Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a ^ b), result);
                    test_failed = test_failed + 1;
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Logical XOR Test Completed.");
        end
    endtask
    
    // 左移运算测试
    task shift_left_test;
        integer j;
        begin
            $display("Running Shift Left Test...");
            for (j = 0; j < 10; j = j + 1) begin
                a = 1 << j;
                b = j;
                op = 4'b0111;
                #10;
                if (result != (a << b)) begin
                    $display("Shift Left Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a << b), result);
                    test_failed = test_failed + 1;
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Shift Left Test Completed.");
        end
    endtask
    
    // 右移运算测试
    task shift_right_test;
        integer j;
        begin
            $display("Running Shift Right Test...");
            for (j = 0; j < 10; j = j + 1) begin
                a = 1 << (j + 5);
                b = j;
                op = 4'b1000;
                #10;
                if (result != (a >> b)) begin
                    $display("Shift Right Test Failed at cycle %0d: Expected 0x%08h, Got 0x%08h", 
                             j, (a >> b), result);
                    test_failed = test_failed + 1;
                end else begin
                    test_passed = test_passed + 1;
                end
            end
            $display("Shift Right Test Completed.");
        end
    endtask
    
    // 零标志位测试
    task zero_flag_test;
        integer j;
        begin
            $display("Running Zero Flag Test...");
            // 测试结果为0的情况
            a = 100;
            b = 100;
            op = 4'b0001; // 减法
            #10;
            if (result != 0) begin
                $display("Zero Flag Test Failed: Expected zero flag but got non-zero result");
                test_failed = test_failed + 1;
            end else begin
                test_passed = test_passed + 1;
            end
            
            // 测试非零结果的情况
            a = 100;
            b = 50;
            op = 4'b0001; // 减法
            #10;
            if (result == 0) begin
                $display("Zero Flag Test Failed: Expected non-zero result but got zero");
                test_failed = test_failed + 1;
            end else begin
                test_passed = test_passed + 1;
            end
            
            $display("Zero Flag Test Completed.");
        end
    endtask
    
    // 边界条件测试
    task boundary_test;
        integer j;
        begin
            $display("Running Boundary Test...");
            
            // 测试最大值
            a = 32'h7FFFFFFF;
            b = 32'h00000001;
            op = 4'b0000; // 加法
            #10;
            if (result != 32'h80000000) begin
                $display("Boundary Test Failed: Max Value Addition");
                test_failed = test_failed + 1;
            end else begin
                test_passed = test_passed + 1;
            end
            
            // 测试最小值
            a = 32'h80000000;
            b = 32'h00000001;
            op = 4'b0001; // 减法
            #10;
            if (result != 32'h7FFFFFFF) begin
                $display("Boundary Test Failed: Min Value Subtraction");
                test_failed = test_failed + 1;
            end else begin
                test_passed = test_passed + 1;
            end
            
            // 测试全零
            a = 32'h00000000;
            b = 32'h00000000;
            op = 4'b0000; // 加法
            #10;
            if (result != 32'h00000000) begin
                $display("Boundary Test Failed: Zero Addition");
                test_failed = test_failed + 1;
            end else begin
                test_passed = test_passed + 1;
            end
            
            $display("Boundary Test Completed.");
        end
    endtask

endmodule