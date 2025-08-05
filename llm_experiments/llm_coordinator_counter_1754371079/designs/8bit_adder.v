module eight_bit_adder (
    input [7:0] a,          // 8位输入a
    input [7:0] b,          // 8位输入b
    input cin,              // 进位输入
    output [7:0] sum,       // 8位和输出
    output cout,            // 进位输出
    output overflow         // 溢出标志
);

    // 9位中间结果，用于计算和进位
    wire [8:0] result;
    
    // 计算加法结果（9位）
    assign result = a + b + cin;
    
    // 输出8位和
    assign sum = result[7:0];
    
    // 进位输出
    assign cout = result[8];
    
    // 溢出检测
    // 溢出发生在两个同号数相加得到异号结果时
    // 即：(a[7] == b[7]) && (a[7] != sum[7])
    assign overflow = (a[7] & b[7] & ~sum[7]) | (~a[7] & ~b[7] & sum[7]);

endmodule