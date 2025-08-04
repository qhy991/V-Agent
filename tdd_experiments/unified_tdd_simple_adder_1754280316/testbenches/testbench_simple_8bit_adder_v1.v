module testbench_simple_8bit_adder;

    // 测试信号
    reg  [7:0] a;
    reg  [7:0] b;
    reg        cin;
    wire [7:0] sum;
    wire       cout;

    // 实例化被测模块
    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    // 测试向量
    initial begin
        $display("开始测试 8 位加法器");
        $monitor("时间 %0t: a=%b, b=%b, cin=%b -> sum=%b, cout=%b", $time, a, b, cin, sum, cout);

        // 基本功能测试
        a = 8'd0; b = 8'd0; cin = 1'b0; #10;
        a = 8'd1; b = 8'd0; cin = 1'b0; #10;
        a = 8'd0; b = 8'd1; cin = 1'b0; #10;
        a = 8'd1; b = 8'd1; cin = 1'b0; #10;
        a = 8'd255; b = 8'd0; cin = 1'b0; #10;
        a = 8'd0; b = 8'd255; cin = 1'b0; #10;
        a = 8'd255; b = 8'd255; cin = 1'b0; #10;
        a = 8'd128; b = 8'd127; cin = 1'b1; #10;
        
        // 进位测试
        a = 8'd255; b = 8'd1; cin = 1'b0; #10;
        a = 8'd255; b = 8'd1; cin = 1'b1; #10;
        
        $display("测试完成");
        $finish;
    end

endmodule