module eight_bit_adder_tb;

    // 声明输入输出信号
    reg [7:0] a;
    reg [7:0] b;
    reg cin;
    wire [7:0] sum;
    wire cout;
    wire overflow;
    
    // 实例化被测模块
    eight_bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );
    
    // 初始化仿真
    initial begin
        $display("Starting 8-bit Adder Testbench");
        $display("Time\t\tA\t\tB\t\tCin\t\tSum\t\tCout\t\tOverflow");
        $display("====\t\t=\t\t=\t\t===\t\t===\t\t====\t\t=======");
        
        // 测试用例1：基本加法
        a = 8'b00000001; b = 8'b00000001; cin = 1'b0;
        #10;
        $display("%0t\t\t%0d\t\t%0d\t\t%0b\t\t%0d\t\t%0b\t\t%0b", $time, a, b, cin, sum, cout, overflow);
        
        // 测试用例2：进位产生
        a = 8'b11111111; b = 8'b00000001; cin = 1'b0;
        #10;
        $display("%0t\t\t%0d\t\t%0d\t\t%0b\t\t%0d\t\t%0b\t\t%0b", $time, a, b, cin, sum, cout, overflow);
        
        // 测试用例3：溢出检测（正数+正数=负数）
        a = 8'b01111111; b = 8'b00000001; cin = 1'b0;
        #10;
        $display("%0t\t\t%0d\t\t%0d\t\t%0b\t\t%0d\t\t%0b\t\t%0b", $time, a, b, cin, sum, cout, overflow);
        
        // 测试用例4：溢出检测（负数+负数=正数）
        a = 8'b10000000; b = 8'b11111111; cin = 1'b0;
        #10;
        $display("%0t\t\t%0d\t\t%0d\t\t%0b\t\t%0d\t\t%0b\t\t%0b", $time, a, b, cin, sum, cout, overflow);
        
        // 测试用例5：带进位输入的加法
        a = 8'b00000001; b = 8'b00000001; cin = 1'b1;
        #10;
        $display("%0t\t\t%0d\t\t%0d\t\t%0b\t\t%0d\t\t%0b\t\t%0b", $time, a, b, cin, sum, cout, overflow);
        
        // 测试用例6：零输入
        a = 8'b00000000; b = 8'b00000000; cin = 1'b0;
        #10;
        $display("%0t\t\t%0d\t\t%0d\t\t%0b\t\t%0d\t\t%0b\t\t%0b", $time, a, b, cin, sum, cout, overflow);
        
        // 测试用例7：最大值加法
        a = 8'b11111111; b = 8'b11111111; cin = 1'b0;
        #10;
        $display("%0t\t\t%0d\t\t%0d\t\t%0b\t\t%0d\t\t%0b\t\t%0b", $time, a, b, cin, sum, cout, overflow);
        
        // 测试用例8：随机测试
        a = $random; b = $random; cin = $random;
        #10;
        $display("%0t\t\t%0d\t\t%0d\t\t%0b\t\t%0d\t\t%0b\t\t%0b", $time, a, b, cin, sum, cout, overflow);
        
        $display("Testbench completed");
        $finish;
    end
    
endmodule