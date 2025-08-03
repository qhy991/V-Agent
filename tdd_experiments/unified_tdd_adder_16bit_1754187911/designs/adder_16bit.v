module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

// 组合逻辑实现16位加法器（行波进位结构）
wire [16:0] internal_sum;
assign internal_sum[0] = cin;

// 逐位全加器链
genvar i;
for (i = 0; i < 16; i = i + 1) begin
    assign internal_sum[i+1] = (a[i] ^ b[i] ^ internal_sum[i]) ? 1'b1 : 1'b0;
end

// 输出赋值
assign sum = internal_sum[15:0];
assign cout = internal_sum[16];

// 溢出检测：两个同号数相加，结果符号相反则溢出
// 有符号比较：最高位为符号位
assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);

endmodule