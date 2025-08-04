`timescale 1ns/1ps

module tb_alu_32bit;

    // 信号声明
    reg [31:0] a;
    reg [31:0] b;
    reg [3:0]  op;
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

    // 测试激励
    initial begin
        // 初始化
        a = 32'h0;
        b = 32'h0;
        op = 4'h0;
        
        // 开始波形记录
        $dumpfile("alu_32bit.vcd");
        $dumpvars(0, tb_alu_32bit);
        
        $display("开始ALU测试...");
        
        // 测试加法
        #10 a = 32'h00000005; b = 32'h00000003; op = 4'h0;
        #10 if (result !== 32'h00000008) $display("加法测试失败");
        
        // 测试减法
        #10 a = 32'h00000005; b = 32'h00000003; op = 4'h1;
        #10 if (result !== 32'h00000002) $display("减法测试失败");
        
        // 测试逻辑与
        #10 a = 32'h0000000F; b = 32'h0000000A; op = 4'h2;
        #10 if (result !== 32'h0000000A) $display("逻辑与测试失败");
        
        // 测试逻辑或
        #10 a = 32'h0000000F; b = 32'h0000000A; op = 4'h3;
        #10 if (result !== 32'h0000000F) $display("逻辑或测试失败");
        
        // 测试异或
        #10 a = 32'h0000000F; b = 32'h0000000A; op = 4'h4;
        #10 if (result !== 32'h00000005) $display("异或测试失败");
        
        // 测试左移
        #10 a = 32'h00000001; b = 32'h00000002; op = 4'h5;
        #10 if (result !== 32'h00000004) $display("左移测试失败");
        
        // 测试右移
        #10 a = 32'h00000004; b = 32'h00000001; op = 4'h6;
        #10 if (result !== 32'h00000002) $display("右移测试失败");
        
        // 测试无效操作码
        #10 a = 32'h00000001; b = 32'h00000001; op = 4'hF;
        #10 if (result !== 32'h00000000) $display("无效操作码测试失败");
        
        // 测试零标志
        #10 a = 32'h00000000; b = 32'h00000000; op = 4'h0;
        #10 if (zero !== 1'b1) $display("零标志测试失败");
        
        $display("ALU测试完成");
        $finish;
    end

endmodule
