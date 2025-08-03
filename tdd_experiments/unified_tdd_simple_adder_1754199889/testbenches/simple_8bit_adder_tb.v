`timescale 1ns / 1ps

module tb_simple_8bit_adder;

    reg [7:0] a;
    reg [7:0] b;
    reg cin;
    wire [7:0] sum;
    wire cout;

    // 实例化被测模块
    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    // 时钟生成
    parameter CLK_PERIOD = 10;
    reg clk;
    always # (CLK_PERIOD/2) clk = ~clk;

    // 复位信号
    reg rst_n;
    initial begin
        rst_n = 0;
        #20;
        rst_n = 1;
    end

    // 波形转储
    initial begin
        $dumpfile("tb_simple_8bit_adder.vcd");
        $dumpvars(0, tb_simple_8bit_adder);
    end

    // 监视信号
    initial begin
        $monitor("%t | a=%d, b=%d, cin=%b | sum=%d, cout=%b", $time, a, b, cin, sum, cout);
    end

    // 测试激励
    initial begin
        // 初始化
        a = 0; b = 0; cin = 0;

        // 等待复位释放
        @(posedge clk);

        // 测试1: 最小值
        a = 8'd0; b = 8'd0; cin = 1'b0;
        @(posedge clk);
        #5;
        if (sum !== 8'd0 || cout !== 1'b0) begin
            $display("ERROR: Test 1 failed. Expected sum=0, cout=0, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test 1 - Min value passed.");
        end

        // 测试2: 最大值（溢出）
        a = 8'd255; b = 8'd255; cin = 1'b1;
        @(posedge clk);
        #5;
        if (sum !== 8'd255 || cout !== 1'b1) begin
            $display("ERROR: Test 2 failed. Expected sum=255, cout=1, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test 2 - Max value with overflow passed.");
        end

        // 测试3: 进位传播
        a = 8'd255; b = 8'd0; cin = 1'b1;
        @(posedge clk);
        #5;
        if (sum !== 8'd0 || cout !== 1'b1) begin
            $display("ERROR: Test 3 failed. Expected sum=0, cout=1, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test 3 - Carry propagation passed.");
        end

        // 测试4: 中间值（进位）
        a = 8'd128; b = 8'd127; cin = 1'b1;
        @(posedge clk);
        #5;
        if (sum !== 8'd0 || cout !== 1'b1) begin
            $display("ERROR: Test 4 failed. Expected sum=0, cout=1, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test 4 - Middle value with carry passed.");
        end

        // 测试5: 无进位
        a = 8'd100; b = 8'd50; cin = 1'b0;
        @(posedge clk);
        #5;
        if (sum !== 8'd150 || cout !== 1'b0) begin
            $display("ERROR: Test 5 failed. Expected sum=150, cout=0, got sum=%d, cout=%b", sum, cout);
        end else begin
            $display("PASS: Test 5 - No carry passed.");
        end

        // 完成测试
        #100;
        $display("All tests completed.");
        $finish;
    end

endmodule