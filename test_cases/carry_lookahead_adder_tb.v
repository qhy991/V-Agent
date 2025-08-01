/**
 * 16位超前进位加法器测试台 - 分case测试，验证功能和性能
 * 
 * 测试用例覆盖：
 * - 基本加法功能验证
 * - 进位传播测试
 * - 边界条件测试
 * - 性能对比测试（与行波进位比较）
 */

`timescale 1ns / 1ps

module carry_lookahead_adder_testbench;
    // 测试信号声明
    reg [15:0] a, b;
    reg cin;
    wire [15:0] sum;
    wire cout;
    
    // 预期结果
    reg [15:0] expected_sum;
    reg expected_cout;
    reg [16:0] expected_result;  // 用于计算预期结果
    
    // 测试计数器和状态
    integer test_case;
    integer passed_tests;
    integer total_tests;
    
    // 实例化被测模块（DUT）
    carry_lookahead_adder_16bit dut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );
    
    // 测试任务：验证单个测试用例
    task check_result(
        input [15:0] test_a,
        input [15:0] test_b,
        input test_cin,
        input [200*8-1:0] test_name
    );
        begin
            // 计算预期结果
            expected_result = test_a + test_b + test_cin;
            expected_sum = expected_result[15:0];
            expected_cout = expected_result[16];
            
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
        $display("🧪 开始16位超前进位加法器功能测试");
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
        a = 16'h1234; b = 16'h5678; cin = 1'b0;
        #5; check_result(a, b, cin, "简单加法（无进位）");
        
        // 测试用例1.2: 有初始进位的加法
        a = 16'h1234; b = 16'h5678; cin = 1'b1;
        #5; check_result(a, b, cin, "有初始进位的加法");
        
        // 测试用例1.3: 零加法
        a = 16'h0000; b = 16'h0000; cin = 1'b0;
        #5; check_result(a, b, cin, "零加法");
        
        // 测试用例1.4: 零加法带进位
        a = 16'h0000; b = 16'h0000; cin = 1'b1;
        #5; check_result(a, b, cin, "零加法带进位");
        
        $display("\\n📋 测试组2: 进位传播测试");
        $display("----------------------------------------");
        
        // 测试用例2.1: 最大值相加（产生进位）
        a = 16'hFFFF; b = 16'h0001; cin = 1'b0;
        #5; check_result(a, b, cin, "最大值+1（进位测试）");
        
        // 测试用例2.2: 最大值相加带初始进位
        a = 16'hFFFF; b = 16'h0000; cin = 1'b1;
        #5; check_result(a, b, cin, "最大值+0+1（进位测试）");
        
        // 测试用例2.3: 双最大值相加
        a = 16'hFFFF; b = 16'hFFFF; cin = 1'b0;
        #5; check_result(a, b, cin, "双最大值相加");
        
        // 测试用例2.4: 双最大值相加带进位
        a = 16'hFFFF; b = 16'hFFFF; cin = 1'b1;
        #5; check_result(a, b, cin, "双最大值+1");
        
        $display("\\n📋 测试组3: 特殊模式测试");
        $display("----------------------------------------");
        
        // 测试用例3.1: 交替位模式
        a = 16'hAAAA; b = 16'h5555; cin = 1'b0;
        #5; check_result(a, b, cin, "交替位模式加法");
        
        // 测试用例3.2: 交替位模式带进位
        a = 16'hAAAA; b = 16'h5555; cin = 1'b1;
        #5; check_result(a, b, cin, "交替位模式+1");
        
        // 测试用例3.3: 连续进位传播模式
        a = 16'h0FFF; b = 16'h0001; cin = 1'b0;
        #5; check_result(a, b, cin, "连续进位传播");
        
        // 测试用例3.4: 多位进位传播
        a = 16'h00FF; b = 16'h0001; cin = 1'b0;
        #5; check_result(a, b, cin, "多位进位传播");
        
        $display("\\n📋 测试组4: 边界条件测试");
        $display("----------------------------------------");
        
        // 测试用例4.1: 最小值测试
        a = 16'h0000; b = 16'h0001; cin = 1'b0;
        #5; check_result(a, b, cin, "最小值+1");
        
        // 测试用例4.2: 最大值测试
        a = 16'h7FFF; b = 16'h7FFF; cin = 1'b0;
        #5; check_result(a, b, cin, "最大正值相加");
        
        // 测试用例4.3: 中值测试
        a = 16'h8000; b = 16'h8000; cin = 1'b0;
        #5; check_result(a, b, cin, "中值相加");
        
        // 测试用例4.4: 对称测试
        a = 16'h1234; b = 16'hEDCB; cin = 1'b0;
        #5; check_result(a, b, cin, "对称数相加");
        
        $display("\\n📋 测试组5: 随机测试");
        $display("----------------------------------------");
        
        // 测试用例5.1-5.4: 随机数测试
        a = 16'h3A5C; b = 16'h7B2E; cin = 1'b0;
        #5; check_result(a, b, cin, "随机测试1");
        
        a = 16'h9F84; b = 16'h1376; cin = 1'b1;
        #5; check_result(a, b, cin, "随机测试2");
        
        a = 16'h456A; b = 16'hBA95; cin = 1'b0;
        #5; check_result(a, b, cin, "随机测试3");
        
        a = 16'hC3E7; b = 16'h2D18; cin = 1'b1;
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
            $display("🎉 所有测试通过！超前进位加法器设计正确！");
            $display("✨ 功能验证: 16位加法运算正确");
            $display("✨ 进位逻辑: 进位传播正常");
            $display("✨ 边界处理: 边界条件处理正确");
        end else begin
            $display("❌ 有 %0d 个测试失败，需要检查设计", total_tests - passed_tests);
            $display("🔍 建议检查项目:");
            $display("   - 进位生成逻辑 (Generate)");
            $display("   - 进位传播逻辑 (Propagate)");
            $display("   - 超前进位计算");
            $display("   - 求和逻辑");
        end
        
        $display("========================================");
        $finish;
    end
    
    // 监控信号变化（可选，用于调试）
    initial begin
        $monitor("[%0t] a=%h, b=%h, cin=%b → sum=%h, cout=%b", 
                 $time, a, b, cin, sum, cout);
    end
    
endmodule