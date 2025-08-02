`timescale 1ns / 1ps

//==============================================================================
// 8位计数器测试台
// 文件名: counter_8bit_tb.v
// 功能: 对 counter_8bit 模块进行全面功能验证
//==============================================================================

module counter_8bit_tb;

    // 测试台信号声明
    reg        clk;       // 时钟
    reg        rst_n;     // 异步复位（低电平有效）
    reg        enable;    // 计数使能
    reg        up_down;   // 计数方向(1:上计数, 0:下计数)
    wire [7:0] count;     // 计数值
    wire       overflow;  // 溢出标志

    // 测试控制变量
    integer test_case = 0;
    integer error_count = 0;
    integer pass_count = 0;

    // 实例化被测模块
    counter_8bit uut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .up_down(up_down),
        .count(count),
        .overflow(overflow)
    );

    // 时钟生成 - 100MHz (10ns周期)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // 主测试序列
    initial begin
        // 初始化波形文件
        $dumpfile("counter_8bit_tb.vcd");
        $dumpvars(0, counter_8bit_tb);
        
        // 打印测试开始信息
        $display("=================================================================");
        $display("开始8位计数器功能测试");
        $display("测试时间: %0t", $time);
        $display("=================================================================");
        
        // 初始化信号
        rst_n = 0;
        enable = 0;
        up_down = 1;
        
        // 等待几个时钟周期
        repeat(5) @(posedge clk);
        
        // 测试用例1: 异步复位功能测试
        test_case = 1;
        test_async_reset();
        
        // 测试用例2: 上计数功能测试
        test_case = 2;
        test_up_counting();
        
        // 测试用例3: 下计数功能测试
        test_case = 3;
        test_down_counting();
        
        // 测试用例4: 使能控制测试
        test_case = 4;
        test_enable_control();
        
        // 测试用例5: 上计数溢出测试
        test_case = 5;
        test_up_overflow();
        
        // 测试用例6: 下计数溢出测试
        test_case = 6;
        test_down_overflow();
        
        // 测试用例7: 边界条件测试
        test_case = 7;
        test_boundary_conditions();
        
        // 测试用例8: 计数方向切换测试
        test_case = 8;
        test_direction_switching();
        
        // 测试用例9: 复位期间使能测试
        test_case = 9;
        test_reset_during_enable();
        
        // 测试总结
        print_test_summary();
        
        // 结束仿真
        $finish;
    end

    //==========================================================================
    // 测试用例1: 异步复位功能测试
    //==========================================================================
    task test_async_reset;
        begin
            $display("\n--- 测试用例1: 异步复位功能测试 ---");
            
            // 设置初始状态
            rst_n = 1;
            enable = 1;
            up_down = 1;
            
            // 等待几个时钟周期让计数器计数
            repeat(10) @(posedge clk);
            
            // 在任意时刻施加复位
            #3; // 在时钟边沿之间施加复位
            rst_n = 0;
            
            // 检查复位是否立即生效
            #1;
            if (count !== 8'h00) begin
                $display("❌ 错误: 异步复位失败, 期望值: 0x00, 实际值: 0x%02h", count);
                error_count = error_count + 1;
            end else begin
                $display("✅ 通过: 异步复位功能正常");
                pass_count = pass_count + 1;
            end
            
            // 保持复位几个时钟周期
            repeat(3) @(posedge clk);
            
            // 释放复位
            rst_n = 1;
            repeat(2) @(posedge clk);
        end
    endtask

    //==========================================================================
    // 测试用例2: 上计数功能测试
    //==========================================================================
    task test_up_counting;
        integer i;
        begin
            $display("\n--- 测试用例2: 上计数功能测试 ---");
            
            // 初始化
            rst_n = 0;
            repeat(2) @(posedge clk);
            rst_n = 1;
            
            enable = 1;
            up_down = 1; // 上计数
            
            // 测试连续上计数
            for (i = 0; i < 20; i = i + 1) begin
                @(posedge clk);
                #1; // 等待信号稳定
                if (count !== i[7:0]) begin
                    $display("❌ 错误: 上计数错误, 期望值: 0x%02h, 实际值: 0x%02h", 
                             i[7:0], count);
                    error_count = error_count + 1;
                end
            end
            
            if (error_count == 0) begin
                $display("✅ 通过: 上计数功能正常 (0-19)");
                pass_count = pass_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 测试用例3: 下计数功能测试
    //==========================================================================
    task test_down_counting;
        integer i;
        begin
            $display("\n--- 测试用例3: 下计数功能测试 ---");
            
            // 先计数到某个值
            rst_n = 0;
            repeat(2) @(posedge clk);
            rst_n = 1;
            
            enable = 1;
            up_down = 1; // 先上计数到20
            repeat(20) @(posedge clk);
            
            // 切换到下计数
            up_down = 0;
            
            // 测试连续下计数
            for (i = 19; i >= 0; i = i - 1) begin
                @(posedge clk);
                #1; // 等待信号稳定
                if (count !== i[7:0]) begin
                    $display("❌ 错误: 下计数错误, 期望值: 0x%02h, 实际值: 0x%02h", 
                             i[7:0], count);
                    error_count = error_count + 1;
                end
            end
            
            if (error_count == 0) begin
                $display("✅ 通过: 下计数功能正常 (19-0)");
                pass_count = pass_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 测试用例4: 使能控制测试
    //==========================================================================
    task test_enable_control;
        reg [7:0] saved_count;
        begin
            $display("\n--- 测试用例4: 使能控制测试 ---");
            
            // 初始化
            rst_n = 0;
            repeat(2) @(posedge clk);
            rst_n = 1;
            
            enable = 1;
            up_down = 1;
            
            // 计数几次
            repeat(5) @(posedge clk);
            saved_count = count;
            
            // 禁用计数器
            enable = 0;
            
            // 等待几个时钟周期，检查计数器是否停止
            repeat(10) @(posedge clk);
            
            if (count !== saved_count) begin
                $display("❌ 错误: 使能控制失败, 期望值: 0x%02h, 实际值: 0x%02h", 
                         saved_count, count);
                error_count = error_count + 1;
            end else begin
                $display("✅ 通过: 使能控制功能正常");
                pass_count = pass_count + 1;
            end
            
            // 重新使能
            enable = 1;
            repeat(3) @(posedge clk);
        end
    endtask

    //==========================================================================
    // 测试用例5: 上计数溢出测试
    //==========================================================================
    task test_up_overflow;
        begin
            $display("\n--- 测试用例5: 上计数溢出测试 ---");
            
            // 初始化到接近最大值
            rst_n = 0;
            repeat(2) @(posedge clk);
            rst_n = 1;
            
            enable = 1;
            up_down = 1;
            
            // 快速计数到253
            repeat(253) @(posedge clk);
            
            // 检查254的值
            @(posedge clk);
            #1;
            if (count !== 8'hFE) begin
                $display("❌ 错误: 计数到254错误, 期望值: 0xFE, 实际值: 0x%02h", count);
                error_count = error_count + 1;
            end
            
            // 检查255的值和溢出标志
            @(posedge clk);
            #1;
            if (count !== 8'hFF) begin
                $display("❌ 错误: 计数到255错误, 期望值: 0xFF, 实际值: 0x%02h", count);
                error_count = error_count + 1;
            end
            
            if (overflow !== 1'b1) begin
                $display("❌ 错误: 255时溢出标志错误, 期望值: 1, 实际值: %b", overflow);
                error_count = error_count + 1;
            end
            
            // 检查溢出到0
            @(posedge clk);
            #1;
            if (count !== 8'h00) begin
                $display("❌ 错误: 溢出回零错误, 期望值: 0x00, 实际值: 0x%02h", count);
                error_count = error_count + 1;
            end
            
            if (overflow !== 1'b0) begin
                $display("❌ 错误: 溢出后标志错误, 期望值: 0, 实际值: %b", overflow);
                error_count = error_count + 1;
            end
            
            if (error_count == 0) begin
                $display("✅ 通过: 上计数溢出功能正常");
                pass_count = pass_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 测试用例6: 下计数溢出测试
    //==========================================================================
    task test_down_overflow;
        begin
            $display("\n--- 测试用例6: 下计数溢出测试 ---");
            
            // 初始化到0
            rst_n = 0;
            repeat(2) @(posedge clk);
            rst_n = 1;
            
            enable = 1;
            up_down = 0; // 下计数
            
            // 检查从0开始下计数的溢出
            @(posedge clk);
            #1;
            if (count !== 8'hFF) begin
                $display("❌ 错误: 下计数溢出错误, 期望值: 0xFF, 实际值: 0x%02h", count);
                error_count = error_count + 1;
            end
            
            if (overflow !== 1'b1) begin
                $display("❌ 错误: 下计数溢出标志错误, 期望值: 1, 实际值: %b", overflow);
                error_count = error_count + 1;
            end
            
            // 检查继续下计数
            @(posedge clk);
            #1;
            if (count !== 8'hFE) begin
                $display("❌ 错误: 下计数继续错误, 期望值: 0xFE, 实际值: 0x%02h", count);
                error_count = error_count + 1;
            end
            
            if (overflow !== 1'b0) begin
                $display("❌ 错误: 溢出标志清除错误, 期望值: 0, 实际值: %b", overflow);
                error_count = error_count + 1;
            end
            
            if (error_count == 0) begin
                $display("✅ 通过: 下计数溢出功能正常");
                pass_count = pass_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 测试用例7: 边界条件测试
    //==========================================================================
    task test_boundary_conditions;
        begin
            $display("\n--- 测试用例7: 边界条件测试 ---");
            
            // 测试在边界值附近的行为
            rst_n = 0;
            repeat(2) @(posedge clk);
            rst_n = 1;
            
            enable = 1;
            up_down = 1;
            
            // 计数到254
            repeat(254) @(posedge clk);
            
            // 测试254->255->0的转换
            @(posedge clk); // 到255
            #1;
            check_value(8'hFF, "边界测试255");
            check_overflow(1'b1, "边界测试255溢出标志");
            
            @(posedge clk); // 到0
            #1;
            check_value(8'h00, "边界测试溢出到0");
            check_overflow(1'b0, "边界测试溢出标志清除");
            
            @(posedge clk); // 到1
            #1;
            check_value(8'h01, "边界测试0到1");
            
            // 切换到下计数测试1->0->255
            up_down = 0;
            @(posedge clk); // 到0
            #1;
            check_value(8'h00, "边界下计数到0");
            
            @(posedge clk); // 到255
            #1;
            check_value(8'hFF, "边界下计数溢出到255");
            check_overflow(1'b1, "边界下计数溢出标志");
            
            if (error_count == 0) begin
                $display("✅ 通过: 边界条件测试正常");
                pass_count = pass_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 测试用例8: 计数方向切换测试
    //==========================================================================
    task test_direction_switching;
        begin
            $display("\n--- 测试用例8: 计数方向切换测试 ---");
            
            // 初始化到中间值
            rst_n = 0;
            repeat(2) @(posedge clk);
            rst_n = 1;
            
            enable = 1;
            up_down = 1;
            
            // 计数到128
            repeat(128) @(posedge clk);
            
            // 频繁切换方向
            up_down = 0; // 下计数
            @(posedge clk);
            #1;
            check_value(8'd127, "方向切换下计数");
            
            up_down = 1; // 上计数
            @(posedge clk);
            #1;
            check_value(8'd128, "方向切换上计数");
            
            up_down = 0; // 下计数
            @(posedge clk);
            #1;
            check_value(8'd127, "再次方向切换下计数");
            
            if (error_count == 0) begin
                $display("✅ 通过: 计数方向切换测试正常");
                pass_count = pass_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 测试用例9: 复位期间使能测试
    //==========================================================================
    task test_reset_during_enable;
        begin
            $display("\n--- 测试用例9: 复位期间使能测试 ---");
            
            // 设置使能和计数方向
            enable = 1;
            up_down = 1;
            rst_n = 1;
            
            // 计数几次
            repeat(10) @(posedge clk);
            
            // 在使能期间施加复位
            rst_n = 0;
            #1;
            check_value(8'h00, "复位期间使能测试");
            
            // 保持复位几个周期
            repeat(3) @(posedge clk);
            check_value(8'h00, "复位期间保持零值");
            
            // 释放复位，检查是否正常计数
            rst_n = 1;
            @(posedge clk);
            #1;
            check_value(8'h01, "复位释放后开始计数");
            
            if (error_count == 0) begin
                $display("✅ 通过: 复位期间使能测试正常");
                pass_count = pass_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 辅助函数: 检查计数值
    //==========================================================================
    task check_value;
        input [7:0] expected;
        input [200*8:1] test_name;
        begin
            if (count !== expected) begin
                $display("❌ 错误: %s, 期望值: 0x%02h, 实际值: 0x%02h", 
                         test_name, expected, count);
                error_count = error_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 辅助函数: 检查溢出标志
    //==========================================================================
    task check_overflow;
        input expected;
        input [200*8:1] test_name;
        begin
            if (overflow !== expected) begin
                $display("❌ 错误: %s, 期望值: %b, 实际值: %b", 
                         test_name, expected, overflow);
                error_count = error_count + 1;
            end
        end
    endtask

    //==========================================================================
    // 测试总结
    //==========================================================================
    task print_test_summary;
        begin
            $display("\n=================================================================");
            $display("8位计数器测试完成");
            $display("=================================================================");
            $display("测试用例总数: %0d", pass_count + error_count);
            $display("通过测试: %0d", pass_count);
            $display("失败测试: %0d", error_count);
            
            if (error_count == 0) begin
                $display("🎉 所有测试通过! 8位计数器功能正常");
            end else begin
                $display("⚠️  发现 %0d 个错误，请检查设计", error_count);
            end
            
            $display("测试结束时间: %0t", $time);
            $display("=================================================================");
        end
    endtask

    // 监控重要信号变化
    always @(posedge clk) begin
        if (rst_n && enable) begin
            $display("时间: %0t, 计数值: 0x%02h (%0d), 方向: %s, 溢出: %b", 
                     $time, count, count, up_down ? "上计数" : "下计数", overflow);
        end
    end

    // 超时保护
    initial begin
        #1000000; // 1ms 超时
        $display("错误: 测试超时!");
        $finish;
    end

endmodule