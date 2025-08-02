module adder_4bit (
    input  [3:0] a,      // 第一个4位加数
    input  [3:0] b,      // 第二个4位加数
    input       cin,     // 进位输入
    output reg  [3:0] sum,   // 4位加法结果
    output reg    cout     // 最终进位输出
);

    // 定义内部信号
    reg [3:0] carry;

    // 全加器链结构：逐位计算
    always @(a or b or cin) begin
        // 第一位（最低位）
        {carry[0], sum[0]} = a[0] + b[0] + cin;
        
        // 第二位
        {carry[1], sum[1]} = a[1] + b[1] + carry[0];
        
        // 第三位
        {carry[2], sum[2]} = a[2] + b[2] + carry[1];
        
        // 第四位（最高位）
        {carry[3], sum[3]} = a[3] + b[3] + carry[2];
    end

    // 最终进位输出
    assign cout = carry[3];

endmodule

module tb_adder_4bit;

    reg [3:0] a;
    reg [3:0] b;
    reg       cin;
    wire [3:0] sum;
    wire       cout;

    adder_4bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    initial begin
        $monitor("a = %b, b = %b, cin = %b => sum = %b, cout = %b", a, b, cin, sum, cout);

        // 测试用例
        a = 4'b0000; b = 4'b0000; cin = 1'b0; #10;
        a = 4'b0001; b = 4'b0010; cin = 1'b0; #10;
        a = 4'b1111; b = 4'b0001; cin = 1'b0; #10;
        a = 4'b1111; b = 4'b1111; cin = 1'b1; #10;

        $finish;
    end

endmodule