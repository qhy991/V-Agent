module tb_adder_16bit;

    reg [15:0] a, b;
    reg cin;
    wire [15:0] sum;
    wire cout;
    wire overflow;

    // 实例化被测模块
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // 测试用例1：最大值相加，应溢出
        a = 16'hFFFF; b = 16'hFFFF; cin = 1;
        #10;
        $display("Test 1: a=%h, b=%h, cin=%b -> sum=%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        // 测试用例2：最小值相加
        a = 16'h0000; b = 16'h0000; cin = 0;
        #10;
        $display("Test 2: a=%h, b=%h, cin=%b -> sum=%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        // 测试用例3：正数相加不溢出
        a = 16'h7FFF; b = 16'h0001; cin = 0;
        #10;
        $display("Test 3: a=%h, b=%h, cin=%b -> sum=%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        // 测试用例4：负数相加溢出
        a = 16'h8000; b = 16'h8000; cin = 0;
        #10;
        $display("Test 4: a=%h, b=%h, cin=%b -> sum=%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        // 测试用例5：边界情况
        a = 16'h7FFF; b = 16'h0001; cin = 1;
        #10;
        $display("Test 5: a=%h, b=%h, cin=%b -> sum=%h, cout=%b, overflow=%b", a, b, cin, sum, cout, overflow);

        #10;
        $finish;
    end

endmodule