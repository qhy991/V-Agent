/**
 * 32位ALU测试台 - 分case测试，每个case都有标准答案对比
 * 
 * 测试用例覆盖：
 * - 加法运算测试
 * - 减法运算测试  
 * - 逻辑运算测试（AND, OR, XOR）
 * - 移位运算测试（左移, 右移）
 * - 边界条件测试
 */

`timescale 1ns / 1ps

module alu_testbench;
    // 测试信号声明
    reg [31:0] a, b;
    reg [3:0] op;
    wire [31:0] result;
    wire zero;
    
    // 测试计数器和状态
    integer test_case;
    integer passed_tests;
    integer total_tests;
    reg [31:0] expected_result;
    reg expected_zero;
    
    // ALU操作码定义（与设计要求一致）
    parameter OP_ADD = 4'b0000;    // 加法
    parameter OP_SUB = 4'b0001;    // 减法
    parameter OP_AND = 4'b0010;    // 逻辑与
    parameter OP_OR  = 4'b0011;    // 逻辑或
    parameter OP_XOR = 4'b0100;    // 异或
    parameter OP_SLL = 4'b0101;    // 左移
    parameter OP_SRL = 4'b0110;    // 右移
    
    // 实例化被测模块（DUT）
    alu_32bit dut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    // 测试任务：检查单个测试用例
    task check_result(
        input [31:0] expected_res,
        input expected_z,
        input [31:0] test_a,
        input [31:0] test_b,
        input [3:0] test_op,
        input [200*8-1:0] test_name
    );
        begin
            total_tests = total_tests + 1;
            
            if (result === expected_res && zero === expected_z) begin
                $display("✅ PASS - %s: a=%h, b=%h, op=%b → result=%h, zero=%b", 
                         test_name, test_a, test_b, test_op, result, zero);
                passed_tests = passed_tests + 1;
            end else begin
                $display("❌ FAIL - %s: a=%h, b=%h, op=%b", test_name, test_a, test_b, test_op);
                $display("    Expected: result=%h, zero=%b", expected_res, expected_z);
                $display("    Actual:   result=%h, zero=%b", result, zero);
            end
        end
    endtask
    
    // 主测试序列
    initial begin
        $display("========================================");
        $display("🧪 开始32位ALU功能测试");
        $display("========================================");
        
        // 初始化
        test_case = 0;
        passed_tests = 0;
        total_tests = 0;
        a = 0; b = 0; op = 0;
        
        // 等待初始化完成
        #10;
        
        $display("\n📋 测试组1: 加法运算 (OP_ADD = 4'b0000)");
        $display("----------------------------------------");
        
        // 测试用例1.1: 基本加法
        a = 32'h12345678; b = 32'h87654321; op = OP_ADD;
        expected_result = 32'h99999999; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "基本加法");
        
        // 测试用例1.2: 零加法
        a = 32'h00000000; b = 32'h00000000; op = OP_ADD;
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "零加法");
        
        // 测试用例1.3: 溢出加法
        a = 32'hFFFFFFFF; b = 32'h00000001; op = OP_ADD;
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "溢出加法");
        
        $display("\n📋 测试组2: 减法运算 (OP_SUB = 4'b0001)");
        $display("----------------------------------------");
        
        // 测试用例2.1: 基本减法
        a = 32'h87654321; b = 32'h12345678; op = OP_SUB;
        expected_result = 32'h7530ECA9; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "基本减法");
        
        // 测试用例2.2: 结果为零的减法
        a = 32'h12345678; b = 32'h12345678; op = OP_SUB;
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "结果为零减法");
        
        // 测试用例2.3: 负数结果（二补码）
        a = 32'h12345678; b = 32'h87654321; op = OP_SUB;
        expected_result = 32'h8ACF1357; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "负数结果减法");
        
        $display("\n📋 测试组3: 逻辑与运算 (OP_AND = 4'b0010)");
        $display("----------------------------------------");
        
        // 测试用例3.1: 基本与运算
        a = 32'hF0F0F0F0; b = 32'h0F0F0F0F; op = OP_AND;
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "基本与运算");
        
        // 测试用例3.2: 全1与运算
        a = 32'hFFFFFFFF; b = 32'h12345678; op = OP_AND;
        expected_result = 32'h12345678; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "全1与运算");
        
        $display("\n📋 测试组4: 逻辑或运算 (OP_OR = 4'b0011)");
        $display("----------------------------------------");
        
        // 测试用例4.1: 基本或运算
        a = 32'hF0F0F0F0; b = 32'h0F0F0F0F; op = OP_OR;
        expected_result = 32'hFFFFFFFF; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "基本或运算");
        
        // 测试用例4.2: 零或运算
        a = 32'h00000000; b = 32'h00000000; op = OP_OR;
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "零或运算");
        
        $display("\n📋 测试组5: 异或运算 (OP_XOR = 4'b0100)");
        $display("----------------------------------------");
        
        // 测试用例5.1: 基本异或
        a = 32'hF0F0F0F0; b = 32'h0F0F0F0F; op = OP_XOR;
        expected_result = 32'hFFFFFFFF; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "基本异或");
        
        // 测试用例5.2: 相同数异或
        a = 32'h12345678; b = 32'h12345678; op = OP_XOR;
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "相同数异或");
        
        $display("\n📋 测试组6: 左移运算 (OP_SLL = 4'b0101)");
        $display("----------------------------------------");
        
        // 测试用例6.1: 基本左移
        a = 32'h12345678; b = 32'h00000004; op = OP_SLL; // 左移4位
        expected_result = 32'h23456780; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "左移4位");
        
        // 测试用例6.2: 左移到零
        a = 32'h80000000; b = 32'h00000001; op = OP_SLL; // 左移1位
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "左移溢出到零");
        
        $display("\n📋 测试组7: 右移运算 (OP_SRL = 4'b0110)");
        $display("----------------------------------------");
        
        // 测试用例7.1: 基本右移
        a = 32'h12345678; b = 32'h00000004; op = OP_SRL; // 右移4位
        expected_result = 32'h01234567; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "右移4位");
        
        // 测试用例7.2: 右移到零
        a = 32'h00000001; b = 32'h00000001; op = OP_SRL; // 右移1位
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "右移到零");
        
        $display("\n📋 测试组8: 边界条件测试");
        $display("----------------------------------------");
        
        // 测试用例8.1: 最大值加法
        a = 32'h7FFFFFFF; b = 32'h00000001; op = OP_ADD;
        expected_result = 32'h80000000; expected_zero = 1'b0;
        #5; check_result(expected_result, expected_zero, a, b, op, "最大值加法");
        
        // 测试用例8.2: 无效操作码测试
        a = 32'h12345678; b = 32'h87654321; op = 4'b1111; // 无效操作码
        expected_result = 32'h00000000; expected_zero = 1'b1;
        #5; check_result(expected_result, expected_zero, a, b, op, "无效操作码");
        
        // 显示最终测试结果
        #10;
        $display("\n========================================");
        $display("🏁 测试完成统计");
        $display("========================================");
        $display("总测试用例: %0d", total_tests);
        $display("通过测试: %0d", passed_tests);
        $display("失败测试: %0d", total_tests - passed_tests);
        
        if (passed_tests == total_tests) begin
            $display("🎉 所有测试通过！ALU设计正确！");
        end else begin
            $display("❌ 有 %0d 个测试失败，需要检查ALU设计", total_tests - passed_tests);
        end
        
        $display("========================================");
        $finish;
    end
    
    // 监控信号变化（可选，用于调试）
    initial begin
        $monitor("[%0t] a=%h, b=%h, op=%b → result=%h, zero=%b", 
                 $time, a, b, op, result, zero);
    end
    
endmodule