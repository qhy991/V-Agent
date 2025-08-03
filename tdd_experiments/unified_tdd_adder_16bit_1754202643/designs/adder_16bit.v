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

// 内部信号声明：用于行波进位结构的进位链
logic [WIDTH-1:0] carry;

// 行波进位加法器实现（纯组合逻辑）
always_comb begin
    // 初始化最低位进位
    carry[0] = cin;
    
    // 逐位计算和与进位
    for (int i = 0; i < WIDTH; i++) begin
        {carry[i+1], sum[i]} = a[i] + b[i] + carry[i];
    end
    
    // 输出进位为最高位的进位
    cout = carry[WIDTH];
    
    // 有符号溢出判断：当两个同号操作数相加，结果符号与操作数相反时发生溢出
    // 即：(a[WIDTH-1] == b[WIDTH-1]) && (sum[WIDTH-1] != a[WIDTH-1])
    overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
end

endmodule