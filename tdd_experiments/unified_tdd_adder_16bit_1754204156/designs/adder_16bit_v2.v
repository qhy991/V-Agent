module adder_16bit #(
    parameter WIDTH = 16
) (
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input cin,
    output reg [WIDTH-1:0] sum,
    output reg cout,
    output reg overflow
);

// 内部信号声明：用于行波进位加法器的进位链
wire [WIDTH-1:0] carry;

// 生成行波进位加法器的每一位
genvar i;
generate
    // 第一位：a[0] + b[0] + cin
    assign carry[0] = (a[0] & b[0]) | (a[0] & cin) | (b[0] & cin);
    
    // 从第1位到第15位：逐级传递进位
    for (i = 1; i < WIDTH; i = i + 1) begin : gen_carry
        assign carry[i] = (a[i] & b[i]) | (a[i] & carry[i-1]) | (b[i] & carry[i-1]);
    end
endgenerate

// 计算每一位的和（异或运算）
assign sum = a ^ b ^ {carry[WIDTH-2], cin};

// 输出进位：最高位的进位
assign cout = carry[WIDTH-1];

// 溢出检测：有符号数溢出发生在两个同号操作数相加结果符号相反时
// 即：当 a 和 b 同号，且结果与它们符号不同时发生溢出
// 使用符号位比较：a[15] == b[15] 且 a[15] != sum[15]
assign overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);

// 同步逻辑：在复位下清零输出
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // 组合逻辑输出在时钟边沿锁存
        // 注意：sum、cout、overflow 是组合逻辑输出，但需在同步路径中注册
        // 由于要求纯组合逻辑，此处仅做时序注册以符合时钟域要求
        // 实际功能由组合逻辑实现，寄存器用于时序控制
        sum <= sum;
        cout <= cout;
        overflow <= overflow;
    end
end

endmodule