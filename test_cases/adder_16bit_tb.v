`timescale 1ns / 1ps

//========================================================================
// 16位加法器测试台 - 严格按照接口规范设计
//========================================================================
module adder_16bit_tb;

    // 测试台参数
    parameter TEST_CYCLES = 1000;  // 随机测试次数
    
    // 信号声明 - 严格匹配接口规范
    reg  [15:0] a;
    reg  [15:0] b;
    reg         cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;
    
    // 被测模块实例化 - 接口名称必须完全匹配
    adder_16bit dut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );
    
    // 测试变量
    integer i, j;
    reg [16:0] expected_sum;  // 17位用于检查进位
    reg expected_cout;
    reg expected_overflow;
    integer error_count;
    integer pass_count;
    
    // 主测试流程
    initial begin
        $display("=================================================================");
        $display("开始16位加法器功能测试");
        $display("时间: %0t", $time);
        $display("=================================================================");
        
        // 初始化
        a = 0;
        b = 0;
        cin = 0;
        error_count = 0;
        pass_count = 0;
        
        #10;  // 等待信号稳定
        
        // 测试用例1: 基本功能测试
        $display("\n--- 测试用例1: 基本加法功能测试 ---");
        
        // 测试简单情况
        test_addition(16'h0000, 16'h0000, 1'b0, "零加零");
        test_addition(16'h0001, 16'h0001, 1'b0, "1+1");
        test_addition(16'hFFFF, 16'h0001, 1'b0, "最大值+1");
        test_addition(16'h8000, 16'h8000, 1'b0, "负数+负数(溢出)");
        test_addition(16'h7FFF, 16'h0001, 1'b0, "正数最大值+1(溢出)");
        
        // 测试用例2: 进位输入测试
        $display("\n--- 测试用例2: 进位输入测试 ---");
        test_addition(16'h0000, 16'h0000, 1'b1, "0+0+1");
        test_addition(16'hFFFF, 16'h0000, 1'b1, "最大值+0+1");
        test_addition(16'hFFFE, 16'h0001, 1'b1, "FFFE+1+1");
        
        // 测试用例3: 边界值测试
        $display("\n--- 测试用例3: 边界值测试 ---");
        test_addition(16'h0000, 16'hFFFF, 1'b0, "0+最大值");
        test_addition(16'hFFFF, 16'hFFFF, 1'b0, "最大值+最大值");
        test_addition(16'h8000, 16'h7FFF, 1'b0, "最小负数+最大正数");
        test_addition(16'h7FFF, 16'h7FFF, 1'b0, "最大正数+最大正数");
        
        // 测试用例4: 溢出检测专项测试
        $display("\n--- 测试用例4: 溢出检测测试 ---");
        
        // 正溢出测试
        test_overflow(16'h7FFF, 16'h0001, 1'b0, 1'b1, "正溢出: 7FFF+1");
        test_overflow(16'h7000, 16'h1000, 1'b0, 1'b1, "正溢出: 7000+1000"); 
        test_overflow(16'h4000, 16'h4000, 1'b0, 1'b1, "正溢出: 4000+4000");
        
        // 负溢出测试
        test_overflow(16'h8000, 16'h8000, 1'b0, 1'b1, "负溢出: 8000+8000");
        test_overflow(16'h9000, 16'h9000, 1'b0, 1'b1, "负溢出: 9000+9000");
        
        // 无溢出测试
        test_overflow(16'h7FFF, 16'h8000, 1'b0, 1'b0, "无溢出: 7FFF+8000");
        test_overflow(16'h0001, 16'hFFFF, 1'b0, 1'b0, "无溢出: 1+FFFF");
        
        // 测试用例5: 随机数据测试
        $display("\n--- 测试用例5: 随机数据测试 ---");
        $display("执行 %0d 次随机测试...", TEST_CYCLES);
        
        for (i = 0; i < TEST_CYCLES; i = i + 1) begin
            // 生成随机数据
            a = $random;
            b = $random;
            cin = $random & 1'b1;
            
            #1;  // 等待组合逻辑稳定
            
            // 计算期望结果
            expected_sum = a + b + cin;
            expected_cout = expected_sum[16];
            
            // 溢出检测：两个同号数相加结果异号
            expected_overflow = (~a[15] & ~b[15] & sum[15]) | (a[15] & b[15] & ~sum[15]);
            
            // 验证结果
            if (sum !== expected_sum[15:0] || cout !== expected_cout || overflow !== expected_overflow) begin
                $display("❌ 随机测试[%0d]失败: a=0x%04X, b=0x%04X, cin=%b", i, a, b, cin);
                $display("   期望: sum=0x%04X, cout=%b, overflow=%b", expected_sum[15:0], expected_cout, expected_overflow);
                $display("   实际: sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);
                error_count = error_count + 1;
            end else begin
                pass_count = pass_count + 1;
            end
            
            // 每100次测试显示进度
            if ((i + 1) % 100 == 0) begin
                $display("   完成 %0d/%0d 随机测试", i + 1, TEST_CYCLES);
            end
        end
        
        // 测试用例6: 进位链测试
        $display("\n--- 测试用例6: 进位链传播测试 ---");
        
        // 最长进位链测试 - 从最低位一直进位到最高位
        test_addition(16'h7FFF, 16'h0001, 1'b0, "最长进位链");
        test_addition(16'h0FFF, 16'h0001, 1'b0, "中等进位链");
        test_addition(16'h00FF, 16'h0001, 1'b0, "短进位链");
        
        // 测试总结
        $display("\n=================================================================");
        if (error_count == 0) begin
            $display("🎉 所有测试通过! 16位加法器设计功能正确");
            $display("✅ 通过测试: %0d", pass_count);
        end else begin
            $display("❌ 发现 %0d 个错误，需要修复设计", error_count);
            $display("✅ 通过测试: %0d", pass_count);
            $display("❌ 失败测试: %0d", error_count);
        end
        $display("测试完成时间: %0t", $time);
        $display("=================================================================");
        
        // 生成波形文件
        $dumpfile("adder_16bit_tb.vcd");
        $dumpvars(0, adder_16bit_tb);
        
        #100;
        $finish;
    end
    
    // 测试函数：加法运算测试
    task test_addition;
        input [15:0] test_a;
        input [15:0] test_b;
        input test_cin;
        input [200*8-1:0] test_name;
        reg [16:0] exp_sum;
        reg exp_cout;
        reg exp_overflow;
    begin
        a = test_a;
        b = test_b;
        cin = test_cin;
        
        #1;  // 等待组合逻辑稳定
        
        // 计算期望结果
        exp_sum = test_a + test_b + test_cin;
        exp_cout = exp_sum[16];
        exp_overflow = (~test_a[15] & ~test_b[15] & sum[15]) | (test_a[15] & test_b[15] & ~sum[15]);
        
        // 检查结果
        if (sum === exp_sum[15:0] && cout === exp_cout && overflow === exp_overflow) begin
            $display("✅ %0s: 0x%04X + 0x%04X + %b = 0x%04X (cout=%b, overflow=%b)", 
                    test_name, test_a, test_b, test_cin, sum, cout, overflow);
            pass_count = pass_count + 1;
        end else begin
            $display("❌ %0s失败:", test_name);
            $display("   输入: 0x%04X + 0x%04X + %b", test_a, test_b, test_cin);
            $display("   期望: sum=0x%04X, cout=%b, overflow=%b", exp_sum[15:0], exp_cout, exp_overflow);
            $display("   实际: sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);
            error_count = error_count + 1;
        end
    end
    endtask
    
    // 测试函数：溢出检测专项测试
    task test_overflow;
        input [15:0] test_a;
        input [15:0] test_b;
        input test_cin;
        input expected_ovf;
        input [200*8-1:0] test_name;
        reg [16:0] exp_sum;
        reg exp_cout;
    begin
        a = test_a;
        b = test_b;
        cin = test_cin;
        
        #1;  // 等待组合逻辑稳定
        
        // 计算期望结果
        exp_sum = test_a + test_b + test_cin;
        exp_cout = exp_sum[16];
        
        // 检查溢出标志
        if (overflow === expected_ovf) begin
            $display("✅ %0s: overflow=%b (正确)", test_name, overflow);
            pass_count = pass_count + 1;
        end else begin
            $display("❌ %0s失败:", test_name);
            $display("   输入: 0x%04X + 0x%04X + %b", test_a, test_b, test_cin);
            $display("   期望overflow: %b, 实际overflow: %b", expected_ovf, overflow);
            $display("   sum=0x%04X, cout=%b", sum, cout);
            error_count = error_count + 1;
        end
    end
    endtask
    
    // 连续监控 - 检测异常情况
    always @(*) begin
        #0.1;  // 极小延迟，确保在信号变化后检查
        if (^sum === 1'bx || ^cout === 1'bx || ^overflow === 1'bx) begin
            $display("⚠️ 警告: 检测到未定义信号 at time %0t", $time);
            $display("   a=0x%04X, b=0x%04X, cin=%b", a, b, cin);
            $display("   sum=0x%04X, cout=%b, overflow=%b", sum, cout, overflow);
        end
    end

endmodule