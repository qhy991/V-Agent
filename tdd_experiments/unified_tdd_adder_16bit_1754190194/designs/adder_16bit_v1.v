module adder_16bit (
    input  [15:0] a,        // 第一个16位操作数
    input  [15:0] b,        // 第二个16位操作数
    input         cin,      // 输入进位
    output reg [15:0] sum,  // 16位和输出
    output reg      cout,   // 输出进位
    output reg      overflow  // 溢出标志（有符号运算）
);

// 16位加法器：sum = a + b + cin
// 使用行波进位结构实现，兼顾可读性与综合性能
always @(*) begin
    // 初始化输出
    sum = 0;
    cout = 0;
    overflow = 0;

    // 逐位加法，从最低位开始
    // 用临时变量保存每一位的进位
    reg [15:0] carry;
    carry[0] = cin;

    for (int i = 0; i < 16; i = i + 1) begin
        // 当前位的和：a[i] ^ b[i] ^ carry[i]
        sum[i] = a[i] ^ b[i] ^ carry[i];
        // 下一位的进位：(a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i])
        carry[i+1] = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
    end

    // 输出进位为最高位的进位
    cout = carry[16];

    // 溢出检测：当两个同号数相加结果异号时发生溢出
    // 即：a 和 b 同号，但结果与它们符号相反
    // 对于有符号数，符号位是第15位（MSB）
    // 溢出条件：(a[15] == b[15]) && (a[15] != sum[15])
    overflow = (a[15] == b[15]) && (a[15] != sum[15]);
end

endmodule