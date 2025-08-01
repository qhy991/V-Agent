/**
 * 8位加法器测试台 - 简单全面的功能验证
 * 
 * 测试覆盖：
 * - 基本加法运算
 * - 进位处理
 * - 边界条件
 * - 随机测试
 */

`timescale 1ns / 1ps

module simple_8bit_adder_testbench;
    // 测试信号声明
    reg [7:0] a, b;
    reg cin;
    wire [7:0] sum;
    wire cout;
    
    // 预期结果
    reg [7:0] expected_sum;
    reg expected_cout;
    reg [8:0] expected_result;  // 9位用于计算预期结果
    
    // 测试计数器
    integer test_case;
    integer passed_tests;
    integer total_tests;
    
    // 实例化被测模块（DUT）
    simple_8bit_adder dut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );
    
    // 测试任务：验证单个测试用例
    task check_result(
        input [7:0] test_a,
        input [7:0] test_b,
        input test_cin,
        input [200*8-1:0] test_name
    );
        begin
            // 计算预期结果
            expected_result = test_a + test_b + test_cin;
            expected_sum = expected_result[7:0];
            expected_cout = expected_result[8];
            
            total_tests = total_tests + 1;
            
            if (sum === expected_sum && cout === expected_cout) begin
                $display("✅ PASS - %s: a=%h, b=%h, cin=%b → sum=%h, cout=%b", 
                         test_name, test_a, test_b, test_cin, sum, cout);
                passed_tests = passed_tests + 1;
            end else begin
                $display("❌ FAIL - %s: a=%h, b=%h, cin=%b", test_name, test_a, test_b, test_cin);
                $display("    Expected: sum=%h, cout=%b", expected_sum, expected_cout);
                $display("    Actual:   sum=%h, cout=%b", sum, cout);
            end
        end
    endtask
    
    // 主测试序列
    initial begin
        $display("========================================");
        $display("🧪 开始8位加法器功能测试");
        $display("========================================");
        
        // 初始化
        test_case = 0;
        passed_tests = 0;
        total_tests = 0;
        a = 0; b = 0; cin = 0;
        
        // 等待初始化完成
        #10;
        
        $display("\\n📋 测试组1: 基本加法功能");
        $display("----------------------------------------");
        
        // 测试用例1.1: 简单加法（无进位）
        a = 8'h12; b = 8'h34; cin = 1'b0;
        #5; check_result(a, b, cin, "简单加法（无进位）");
        
        // 测试用例1.2: 有初始进位的加法
        a = 8'h12; b = 8'h34; cin = 1'b1;
        #5; check_result(a, b, cin, "有初始进位的加法");
        
        // 测试用例1.3: 零加法
        a = 8'h00; b = 8'h00; cin = 1'b0;
        #5; check_result(a, b, cin, "零加法");
        
        // 测试用例1.4: 零加法带进位
        a = 8'h00; b = 8'h00; cin = 1'b1;
        #5; check_result(a, b, cin, "零加法带进位");
        
        $display("\\n📋 测试组2: 进位测试");
        $display("----------------------------------------");
        
        // 测试用例2.1: 产生进位
        a = 8'hFF; b = 8'h01; cin = 1'b0;
        #5; check_result(a, b, cin, "最大值+1（产生进位）");
        
        // 测试用例2.2: 最大值相加
        a = 8'hFF; b = 8'hFF; cin = 1'b0;
        #5; check_result(a, b, cin, "双最大值相加");
        
        // 测试用例2.3: 最大值相加带进位
        a = 8'hFF; b = 8'hFF; cin = 1'b1;
        #5; check_result(a, b, cin, "双最大值+1");
        
        $display("\\n📋 测试组3: 边界条件测试");
        $display("----------------------------------------");
        
        // 测试用例3.1: 最小值测试
        a = 8'h00; b = 8'h01; cin = 1'b0;
        #5; check_result(a, b, cin, "最小值+1");
        
        // 测试用例3.2: 中值测试
        a = 8'h80; b = 8'h7F; cin = 1'b0;
        #5; check_result(a, b, cin, "中值相加");
        
        // 测试用例3.3: 对称测试
        a = 8'hAA; b = 8'h55; cin = 1'b0;
        #5; check_result(a, b, cin, "对称数相加");
        
        $display("\\n📋 测试组4: 随机测试");
        $display("----------------------------------------");
        
        // 测试用例4.1-4.4: 随机数测试
        a = 8'h3A; b = 8'h7B; cin = 1'b0;
        #5; check_result(a, b, cin, "随机测试1");
        
        a = 8'h9F; b = 8'h13; cin = 1'b1;
        #5; check_result(a, b, cin, "随机测试2");
        
        a = 8'h45; b = 8'hBA; cin = 1'b0;
        #5; check_result(a, b, cin, "随机测试3");
        
        a = 8'hC3; b = 8'h2D; cin = 1'b1;
        #5; check_result(a, b, cin, "随机测试4");
        
        // 显示最终测试结果
        #10;
        $display("\\n========================================");
        $display("🏁 测试完成统计");
        $display("========================================");
        $display("总测试用例: %0d", total_tests);
        $display("通过测试: %0d", passed_tests);
        $display("失败测试: %0d", total_tests - passed_tests);
        
        if (passed_tests == total_tests) begin
            $display("🎉 所有测试通过！8位加法器设计正确！");
            $display("✨ 功能验证: 8位加法运算正确");
            $display("✨ 进位逻辑: 进位处理正常");
            $display("✨ 边界处理: 边界条件处理正确");
        end else begin
            $display("❌ 有 %0d 个测试失败，需要检查设计", total_tests - passed_tests);
            $display("🔍 建议检查项目:");
            $display("   - 加法逻辑实现");
            $display("   - 进位链处理");
            $display("   - 模块接口定义");
        end
        
        $display("========================================");
        $finish;
    end
    
    // 监控信号变化（用于调试）
    initial begin
        $monitor("[%0t] a=%h, b=%h, cin=%b → sum=%h, cout=%b", 
                 $time, a, b, cin, sum, cout);
    end
    
endmodule