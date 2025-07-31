module four_bit_adder_testbench;
    reg [3:0] a;
    reg [3:0] b;
    reg cin;
    wire [3:0] sum;
    wire cout;

    // 实例化被测模块
    four_bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    initial begin
        // 测试用例1: 0 + 0 + 0 = 0
        a = 4'b0000;
        b = 4'b0000;
        cin = 1'b0;
        #10;

        // 测试用例2: 5 + 3 + 0 = 8
        a = 4'b0101;
        b = 4'b0011;
        cin = 1'b0;
        #10;

        // 测试用例3: 15 + 1 + 1 = 17 (溢出)
        a = 4'b1111;
        b = 4'b0001;
        cin = 1'b1;
        #10;

        // 测试用例4: 10 + 6 + 0 = 16
        a = 4'b1010;
        b = 4'b0110;
        cin = 1'b0;
        #10;

        // 测试用例5: 7 + 8 + 0 = 15 (溢出)
        a = 4'b0111;
        b = 4'b1000;
        cin = 1'b0;
        #10;

        // 结束仿真
        $finish;
    end

    // 波形显示
    initial begin
        $dumpfile("four_bit_adder_tb.vcd");
        $dumpvars(0, four_bit_adder_testbench);
    end
endmodule