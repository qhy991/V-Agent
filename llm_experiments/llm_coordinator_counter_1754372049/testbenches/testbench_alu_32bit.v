`timescale 1ns/1ps

module testbench_alu_32bit;

    // 测试信号
    reg [31:0] a;
    reg [31:0] b;
    reg [3:0] op;
    wire [31:0] result;
    wire zero;
    
    // 实例化被测模块
    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    // 测试向量
    initial begin
        // 测试加法操作
        $display("Testing ADD operation...");
        a = 32'h00000005;
        b = 32'h00000003;
        op = 4'b0000;
        #10;
        $display("Result: %h, Zero: %b", result, zero);
        
        // 测试减法操作
        $display("Testing SUB operation...");
        a = 32'h00000008;
        b = 32'h00000003;
        op = 4'b0001;
        #10;
        $display("Result: %h, Zero: %b", result, zero);
        
        // 测试按位与操作
        $display("Testing AND operation...");
        a = 32'h0000000F;
        b = 32'h00000003;
        op = 4'b0010;
        #10;
        $display("Result: %h, Zero: %b", result, zero);
        
        // 测试按位或操作
        $display("Testing OR operation...");
        a = 32'h0000000C;
        b = 32'h00000003;
        op = 4'b0011;
        #10;
        $display("Result: %h, Zero: %b", result, zero);
        
        // 测试按位异或操作
        $display("Testing XOR operation...");
        a = 32'h0000000F;
        b = 32'h00000003;
        op = 4'b0100;
        #10;
        $display("Result: %h, Zero: %b", result, zero);
        
        // 测试左移操作
        $display("Testing SLL operation...");
        a = 32'h00000005;
        b = 32'h00000002;
        op = 4'b0110;
        #10;
        $display("Result: %h, Zero: %b", result, zero);
        
        // 测试右移操作
        $display("Testing SRL operation...");
        a = 32'h00000010;
        b = 32'h00000002;
        op = 4'b0111;
        #10;
        $display("Result: %h, Zero: %b", result, zero);
        
        // 测试零标志位
        $display("Testing zero flag...");
        a = 32'h00000000;
        b = 32'h00000000;
        op = 4'b0000;
        #10;
        $display("Result: %h, Zero: %b", result, zero);
        
        $finish;
    end
    
    // 显示波形
    initial begin
        $dumpfile("alu_32bit.vcd");
        $dumpvars(0, testbench_alu_32bit);
    end
    
endmodule