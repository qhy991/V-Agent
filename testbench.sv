`timescale 1ns/1ps

module testbench;
    // 信号声明
    reg clk;
    reg rst;
    reg [3:0] in;
    wire [4:0] out;

    // 实例化被测模块
    counter uut (
        .clk(clk),
        .rst(rst),
        .in(in),
        .out(out)
    );

    // 生成时钟（周期10ns）
    always #5 clk = ~clk;

    // 测试逻辑
    initial begin
        // 初始化信号
        clk = 0;
        rst = 1;
        in = 4'b0000;

        #10 rst = 0; // 释放复位

        // 验证序列
        @(posedge clk);
        in = 4'b0001;
        @(posedge clk);
        if (out !== 5'b00001) $display("Error at step 1");
        
        @(posedge clk);
        in = 4'b0010;
        @(posedge clk);
        if (out !== 5'b00011) $display("Error at step 2");

        // 结束仿真
        $finish;
    end
endmodule