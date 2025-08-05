`timescale 1ns/1ps

module tb_adder_4bit;

// 信号声明
reg [3:0] a;
reg [3:0] b;
reg       cin;
wire [3:0] sum;
wire       cout;

// 测试控制信号
reg [31:0] passed_count;
reg [31:0] failed_count;
reg [31:0] total_count;
integer    test_number;
integer    i;
integer    j;
integer    k;

// 时钟信号
reg clk;

// 生成时钟
always begin
    #5 clk = ~clk;
end

// 实例化被测模块
adder_4bit uut (
    .a(a),
    .b(b),
    .cin(cin),
    .sum(sum),
    .cout(cout)
);

// 初始化
initial begin
    // 初始化信号
    clk = 0;
    a = 0;
    b = 0;
    cin = 0;
    
    // 初始化计数器
    passed_count = 0;
    failed_count = 0;
    total_count = 0;
    test_number = 0;
    
    // 波形转储
    $dumpfile("adder_4bit.vcd");
    $dumpvars(0, tb_adder_4bit);
    
    // 显示测试开始信息
    $display("==================================================");
    $display("Starting 4-bit Adder Testbench");
    $display("==================================================");
    
    // 等待几个时钟周期确保稳定
    repeat(2) @(posedge clk);
    
    // Test Case 1: Zero Addition
    test_number = test_number + 1;
    total_count = total_count + 1;
    a = 4'b0000;
    b = 4'b0000;
    cin = 1'b0;
    @(posedge clk);
    begin
        reg [4:0] expected;
        reg [4:0] actual;
        expected = 5'b00000;
        actual = {cout, sum};
        if (actual == expected) begin
            $display("Time=%0t: Test Case %0d - zero_addition", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", expected, actual);
            passed_count = passed_count + 1;
        end else begin
            $display("Time=%0t: Test Case %0d - zero_addition", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", expected, actual);
            failed_count = failed_count + 1;
        end
    end
    
    // Test Case 2: Max Values
    test_number = test_number + 1;
    total_count = total_count + 1;
    a = 4'b1111;
    b = 4'b1111;
    cin = 1'b0;
    @(posedge clk);
    begin
        reg [4:0] expected;
        reg [4:0] actual;
        expected = 5'b11110;
        actual = {cout, sum};
        if (actual == expected) begin
            $display("Time=%0t: Test Case %0d - max_values", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", expected, actual);
            passed_count = passed_count + 1;
        end else begin
            $display("Time=%0t: Test Case %0d - max_values", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", expected, actual);
            failed_count = failed_count + 1;
        end
    end
    
    // Test Case 3: Carry Propagation
    test_number = test_number + 1;
    total_count = total_count + 1;
    a = 4'b1111;
    b = 4'b0001;
    cin = 1'b0;
    @(posedge clk);
    begin
        reg [4:0] expected;
        reg [4:0] actual;
        expected = 5'b00000;
        actual = {cout, sum};
        if (actual == expected) begin
            $display("Time=%0t: Test Case %0d - carry_propagation", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", expected, actual);
            passed_count = passed_count + 1;
        end else begin
            $display("Time=%0t: Test Case %0d - carry_propagation", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", expected, actual);
            failed_count = failed_count + 1;
        end
    end
    
    // Test Case 4: With Carry In
    test_number = test_number + 1;
    total_count = total_count + 1;
    a = 4'b1111;
    b = 4'b1111;
    cin = 1'b1;
    @(posedge clk);
    begin
        reg [4:0] expected;
        reg [4:0] actual;
        expected = 5'b11111;
        actual = {cout, sum};
        if (actual == expected) begin
            $display("Time=%0t: Test Case %0d - with_carry_in", $time, test_number);
            $display("Expected: %h, Got: %h, Status: PASS", expected, actual);
            passed_count = passed_count + 1;
        end else begin
            $display("Time=%0t: Test Case %0d - with_carry_in", $time, test_number);
            $display("Expected: %h, Got: %h, Status: FAIL", expected, actual);
            failed_count = failed_count + 1;
        end
    end
    
    // Test Case 5-18: Random Values
    for (i = 0; i < 14; i = i + 1) begin
        test_number = test_number + 1;
        total_count = total_count + 1;
        a = $random & 4'hF;
        b = $random & 4'hF;
        cin = $random & 1'b1;
        @(posedge clk);
        begin
            reg [4:0] expected;
            reg [4:0] actual;
            expected = a + b + cin;
            actual = {cout, sum};
            if (actual == expected) begin
                $display("Time=%0t: Test Case %0d - random_values", $time, test_number);
                $display("Expected: %h, Got: %h, Status: PASS", expected, actual);
                passed_count = passed_count + 1;
            end else begin
                $display("Time=%0t: Test Case %0d - random_values", $time, test_number);
                $display("Expected: %h, Got: %h, Status: FAIL", expected, actual);
                failed_count = failed_count + 1;
            end
        end
    end
    
    // 运行额外的时钟周期以达到500个时钟周期的总仿真时间
    repeat(482) @(posedge clk);
    
    // 输出测试总结
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