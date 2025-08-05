`timescale 1ns / 1ps

module adder_16bit_tb;

    // 参数定义
    parameter CLK_PERIOD = 10.0; // 时钟周期 10ns

    // 信号声明
    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // 被测模块实例化
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // 测试主程序
    initial begin
        $display("=== Starting Testbench for adder_16bit ===");
        
        // 波形转储设置
        $dumpfile("adder_16bit_tb.vcd");
        $dumpvars(0, adder_16bit_tb);
        
        // 初始化输入
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #10;

        // 基本加法测试
        $display("=== Test Case: basic_addition ===");
        a = 16'h0001; b = 16'h0002; cin = 1'b0; #10;
        check_result(a, b, cin, 16'h0003, 1'b0, 1'b0);

        // 进位传播测试
        $display("=== Test Case: carry_propagation ===");
        a = 16'hFFFF; b = 16'h0001; cin = 1'b0; #10;
        check_result(a, b, cin, 16'h0000, 1'b1, 1'b0);

        // 溢出检测测试
        $display("=== Test Case: overflow_detection ===");
        a = 16'h7FFF; b = 16'h0001; cin = 1'b0; #10;
        check_result(a, b, cin, 16'h8000, 1'b0, 1'b1);

        a = 16'h8000; b = 16'hFFFF; cin = 1'b0; #10;
        check_result(a, b, cin, 16'h7FFF, 1'b0, 1'b1);

        // 边界值测试
        $display("=== Test Case: boundary_values ===");
        a = 16'h0000; b = 16'h0000; cin = 1'b0; #10;
        check_result(a, b, cin, 16'h0000, 1'b0, 1'b0);

        a = 16'hFFFF; b = 16'h0000; cin = 1'b0; #10;
        check_result(a, b, cin, 16'hFFFF, 1'b0, 1'b0);

        $display("=== Testbench Finished ===");
        $finish;
    end

    // 结果检查任务
    task check_result;
        input [15:0] a_val, b_val;
        input cin_val;
        input [15:0] expected_sum;
        input expected_cout, expected_overflow;
        
        reg [15:0] actual_sum;
        reg actual_cout, actual_overflow;
        
        begin
            #2; // 等待信号稳定
            
            actual_sum = sum;
            actual_cout = cout;
            actual_overflow = overflow;

            if (actual_sum !== expected_sum) begin
                $display("ERROR: Sum mismatch");
                $display("  a = 0x%04X, b = 0x%04X, cin = %b", a_val, b_val, cin_val);
                $display("  Expected sum = 0x%04X, Actual sum = 0x%04X", expected_sum, actual_sum);
            end else begin
                $display("PASS: Sum matches");
            end

            if (actual_cout !== expected_cout) begin
                $display("ERROR: Cout mismatch");
                $display("  Expected cout = %b, Actual cout = %b", expected_cout, actual_cout);
            end else begin
                $display("PASS: Cout matches");
            end

            if (actual_overflow !== expected_overflow) begin
                $display("ERROR: Overflow mismatch");
                $display("  Expected overflow = %b, Actual overflow = %b", expected_overflow, actual_overflow);
            end else begin
                $display("PASS: Overflow matches");
            end
        end
    endtask

    // 实时监控
    initial begin
        $monitor("Time=%0t | a=0x%04X | b=0x%04X | cin=%b | sum=0x%04X | cout=%b | overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);
    end

endmodule 