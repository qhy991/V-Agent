module four_bit_adder_tb();
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
        $dumpfile("four_bit_adder_tb.vcd");
        $dumpvars(0, four_bit_adder_tb);

        // 测试用例1: 基本功能测试 (0+0+0=0)
        a = 4'b0000;
        b = 4'b0000;
        cin = 1'b0;
        #10;
        $display("Test Case 1: a=0000, b=0000, cin=0 -> sum=0000, cout=0");
        if (sum === 4'b0000 && cout === 1'b0) $display("Pass"); else $display("Fail");

        // 测试用例2: 基本功能测试 (1+1+0=2)
        a = 4'b0001;
        b = 4'b0001;
        cin = 1'b0;
        #10;
        $display("Test Case 2: a=0001, b=0001, cin=0 -> sum=0010, cout=0");
        if (sum === 4'b0010 && cout === 1'b0) $display("Pass"); else $display("Fail");

        // 测试用例3: 边界值测试 (最大值 + 最大值 + 0 = 1111 + 1111 = 11110)
        a = 4'b1111;
        b = 4'b1111;
        cin = 1'b0;
        #10;
        $display("Test Case 3: a=1111, b=1111, cin=0 -> sum=1110, cout=1");
        if (sum === 4'b1110 && cout === 1'b1) $display("Pass"); else $display("Fail");

        // 测试用例4: 边界值测试 (最大值 + 0 + 1 = 1111 + 0000 + 1 = 1111 + 1 = 10000)
        a = 4'b1111;
        b = 4'b0000;
        cin = 1'b1;
        #10;
        $display("Test Case 4: a=1111, b=0000, cin=1 -> sum=0000, cout=1");
        if (sum === 4'b0000 && cout === 1'b1) $display("Pass"); else $display("Fail");

        // 测试用例5: 随机测试 (随机输入)
        a = 4'b1010;
        b = 4'b0101;
        cin = 1'b1;
        #10;
        $display("Test Case 5: a=1010, b=0101, cin=1 -> sum=0000, cout=1");
        if (sum === 4'b0000 && cout === 1'b1) $display("Pass"); else $display("Fail");

        // 测试用例6: 异常情况 (进位溢出)
        a = 4'b1111;
        b = 4'b1111;
        cin = 1'b1;
        #10;
        $display("Test Case 6: a=1111, b=1111, cin=1 -> sum=1111, cout=1");
        if (sum === 4'b1111 && cout === 1'b1) $display("Pass"); else $display("Fail");

        // 结束仿真
        #10;
        $finish;
    end
endmodule