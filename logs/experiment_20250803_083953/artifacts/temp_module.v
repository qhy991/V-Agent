module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    // 16位加法器实现
    wire [15:0] carry;
    assign carry[0] = cin;

    // 计算每一位的和和进位
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : adder_stage
            full_adder fa (
                .a(a[i]),
                .b(b[i]),
                .cin(carry[i]),
                .sum(sum[i]),
                .cout(carry[i+1])
            );
        end
    endgenerate

    // 输出进位
    assign cout = carry[16];

    // 溢出检测：当两个同号数相加结果变号时溢出
    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);

endmodule

// 全加器模块
module full_adder (
    input  a,
    input  b,
    input  cin,
    output sum,
    output cout
);

    wire xor1, xor2;
    wire and1, and2, and3;

    // 计算和
    assign xor1 = a ^ b;
    assign xor2 = xor1 ^ cin;
    assign sum = xor2;

    // 计算进位
    assign and1 = a & b;
    assign and2 = a & cin;
    assign and3 = b & cin;
    assign cout = and1 | and2 | and3;

endmodule