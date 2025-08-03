module adder_16bit #(
    parameter WIDTH = 16
) (
    input               clk,
    input               rst,
    input  [WIDTH-1:0]  a,
    input  [WIDTH-1:0]  b,
    input               cin,
    output logic [WIDTH-1:0] sum,
    output logic        cout,
    output logic        overflow
);

// 内部信号声明
logic [WIDTH-1:0] carry;

// 功能实现：行波进位加法器（Ripple Carry Adder）
// 逐位计算和与进位，从最低位开始
always_comb begin
    // 初始化最低位的进位
    carry[0] = cin;
    
    // 计算每一位的和与进位
    for (int i = 0; i < WIDTH; i++) begin
        sum[i] = a[i] ^ b[i] ^ carry[i];
        carry[i+1] = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
    end
    
    // 输出进位
    cout = carry[WIDTH];
    
    // 有符号溢出检测：当两个同号操作数相加结果符号相反时发生溢出
    // 即：最高位进位与次高位进位不一致
    overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
end

endmodule