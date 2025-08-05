module eight_bit_adder (
    input [7:0] a,          // 8位加数A
    input [7:0] b,          // 8位加数B
    input cin,              // 进位输入
    output [7:0] sum,       // 8位和
    output cout,            // 进位输出
    output overflow         // 溢出标志
);

    // 9位中间结果，用于计算和检测进位
    wire [8:0] result;
    
    // 执行加法运算
    assign result = a + b + cin;
    
    // 提取低8位作为和
    assign sum = result[7:0];
    
    // 提取第8位作为进位输出
    assign cout = result[8];
    
    // 溢出检测逻辑
    // 当两个同符号数相加产生不同符号的结果时发生溢出
    assign overflow = (a[7] == b[7]) && (a[7] != sum[7]);
    
endmodule