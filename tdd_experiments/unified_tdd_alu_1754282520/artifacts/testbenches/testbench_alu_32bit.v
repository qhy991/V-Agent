`timescale 1ns/1ps

module tb_alu_32bit;

    // 信号声明
    reg [31:0] a;
    reg [31:0] b;
    reg [3:0]  op;
    wire [31:0] result;
    wire zero;

    // 时钟和复位信号
    reg clk;
    reg rst_n;

    // 实例化被测模块
    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 10ns周期时钟
    end

    // 复位信号生成
    initial begin
        rst_n = 0;
        #10 rst_n = 1;
    end

    // 测试激励生成
    initial begin
        // 打开波形文件
        $dumpfile("alu_32bit.vcd");
        $dumpvars(0, tb_alu_32bit);

        // 初始化输入信号
        a = 32'h00000000;
        b = 32'h00000000;
        op = 4'b0000;

        // 等待复位完成
        #20;

        // 开始测试
        $display("开始测试 ALU_32BIT 模块");
        $display("时间\tA\t\tB\t\tOP\tRESULT\tZERO");

        // 测试基本算术和逻辑操作
        test_basic_operations();

        // 测试移位操作
        test_shift_operations();

        // 测试边界条件
        test_edge_cases();

        // 结束仿真
        #100;
        $display("测试完成");
        $finish;
    end

    // 基本操作测试
    task test_basic_operations;
        integer i;
        for(i=0; i<5; i=i+1) begin
            case(i)
                0: begin op = 4'b0000; a = 32'h00000005; b = 32'h00000003; end // ADD
                1: begin op = 4'b0001; a = 32'h00000005; b = 32'h00000003; end // SUB
                2: begin op = 4'b0010; a = 32'h0000000F; b = 32'h00000003; end // AND
                3: begin op = 4'b0011; a = 32'h0000000F; b = 32'h00000003; end // OR
                4: begin op = 4'b0100; a = 32'h0000000F; b = 32'h00000003; end // XOR
            endcase
            #10;
            $display("%0t\t%h\t%h\t%b\t%h\t%b", $time, a, b, op, result, zero);
        end
    endtask

    // 移位操作测试
    task test_shift_operations;
        integer i;
        for(i=0; i<2; i=i+1) begin
            case(i)
                0: begin op = 4'b0101; a = 32'h00000005; b = 32'h00000002; end // SLL
                1: begin op = 4'b0110; a = 32'h00000008; b = 32'h00000001; end // SRL
            endcase
            #10;
            $display("%0t\t%h\t%h\t%b\t%h\t%b", $time, a, b, op, result, zero);
        end
    endtask

    // 边界条件测试
    task test_edge_cases;
        integer i;
        for(i=0; i<4; i=i+1) begin
            case(i)
                0: begin op = 4'b0000; a = 32'hFFFFFFFF; b = 32'h00000001; end // ADD最大值
                1: begin op = 4'b0001; a = 32'h00000000; b = 32'h00000001; end // SUB负数
                2: begin op = 4'b0010; a = 32'hFFFFFFFF; b = 32'h00000000; end // AND零
                3: begin op = 4'b0101; a = 32'h00000001; b = 32'h0000001F; end // SLL最大移位
            endcase
            #10;
            $display("%0t\t%h\t%h\t%b\t%h\t%b", $time, a, b, op, result, zero);
        end
    endtask

endmodule