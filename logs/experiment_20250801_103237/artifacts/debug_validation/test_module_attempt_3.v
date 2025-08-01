// 全加器模块定义
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

// 8位加法器模块定义
module simple_8bit_adder (
    input  [7:0] a,         // 第一个8位操作数
    input  [7:0] b,         // 第二个8位操作数
    input        cin,       // 输入进位
    output [7:0] sum,       // 8位和
    output       cout       // 输出进位
);

    // 定义内部信号
    wire [7:0] carry;

    // 使用行波进位链实现8位加法器
    // 第0位
    full_adder fa0 (
        .a(a[0]),
        .b(b[0]),
        .cin(cin),
        .sum(sum[0]),
        .cout(carry[0])
    );

    // 第1位
    full_adder fa1 (
        .a(a[1]),
        .b(b[1]),
        .cin(carry[0]),
        .sum(sum[1]),
        .cout(carry[1])
    );

    // 第2位
    full_adder fa2 (
        .a(a[2]),
        .b(b[2]),
        .cin(carry[1]),
        .sum(sum[2]),
        .cout(carry[2])
    );

    // 第3位
    full_adder fa3 (
        .a(a[3]),
        .b(b[3]),
        .cin(carry[2]),
        .sum(sum[3]),
        .cout(carry[3])
    );

    // 第4位
    full_adder fa4 (
        .a(a[4]),
        .b(b[4]),
        .cin(carry[3]),
        .sum(sum[4]),
        .cout(carry[4])
    );

    // 第5位
    full_adder fa5 (
        .a(a[5]),
        .b(b[5]),
        .cin(carry[4]),
        .sum(sum[5]),
        .cout(carry[5])
    );

    // 第6位
    full_adder fa6 (
        .a(a[6]),
        .b(b[6]),
        .cin(carry[5]),
        .sum(sum[6]),
        .cout(carry[6])
    );

    // 第7位
    full_adder fa7 (
        .a(a[7]),
        .b(b[7]),
        .cin(carry[6]),
        .sum(sum[7]),
        .cout(cout)
    );

endmodule