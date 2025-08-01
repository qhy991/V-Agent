module simple_8bit_adder (
    input  [7:0] a,         // 第一个8位操作数
    input  [7:0] b,         // 第二个8位操作数
    input        cin,       // 输入进位
    output [7:0] sum,       // 8位和
    output       cout       // 输出进位
);

    // 定义内部信号
    wire [7:0] carry;

    // 第一位加法（最低位）
    full_adder fa0 (
        .a(a[0]),
        .b(b[0]),
        .cin(cin),
        .sum(sum[0]),
        .cout(carry[0])
    );

    // 其余7位加法
    genvar i;
    generate
        for (i = 1; i < 8; i = i + 1) begin : gen_full_adders
            full_adder fa (
                .a(a[i]),
                .b(b[i]),
                .cin(carry[i-1]),
                .sum(sum[i]),
                .cout(carry[i])
            );
        end
    endgenerate

    // 输出最终进位
    assign cout = carry[7];

endmodule

// 全加器子模块
module full_adder (
    input  a,
    input  b,
    input  cin,
    output sum,
    output cout
);

    // 计算和
    assign sum = a ^ b ^ cin;

    // 计算进位
    assign cout = (a & b) | (a & cin) | (b & cin);

endmodule