`timescale 1ns / 1ps

module tb_adder_16bit;

    // 时钟周期定义
    parameter CLK_PERIOD = 10.0;

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
        $monitor("Time=%0t, a=0x%04h, b=0x%04h, cin=%b, sum=0x%04h, cout=%b, overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);

        // 初始化输入
        a = 16'h0000;
        b = 16'h0000;
        cin = 1'b0;
        #10;

        // 基本加法测试
        $display("=== Basic Addition Test ===");
        a = 16'h0001; b = 16'h0001; cin = 1'b0; #10;
        a = 16'hFFFF; b = 16'h0001; cin = 1'b0; #10;
        a = 16'h7FFF; b = 16'h0001; cin = 1'b0; #10;

        // 进位传播测试
        $display("=== Carry Propagation Test ===");
        a = 16'h0000; b = 16'h0000; cin = 1'b1; #10;

        // 溢出检测测试
        $display("=== Overflow Detection Test ===");
        a = 16'h7FFF; b = 16'h0001; cin = 1'b0; #10;
        a = 16'h8000; b = 16'h8000; cin = 1'b0; #10;

        // 边界值测试
        $display("=== Boundary Values Test ===");
        a = 16'h0000; b = 16'h0000; cin = 1'b0; #10;
        a = 16'hFFFF; b = 16'h0000; cin = 1'b0; #10;

        $display("Simulation completed.");
        $finish;
    end

    // 波形转储设置
    initial begin
        $dumpfile("tb_adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

endmodule