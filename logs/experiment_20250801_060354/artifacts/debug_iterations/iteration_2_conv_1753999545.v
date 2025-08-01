module carry_lookahead_adder_16bit (
    input  [15:0] a,        // 第一个16位操作数
    input  [15:0] b,        // 第二个16位操作数  
    input         cin,      // 输入进位
    output [15:0] sum,      // 16位和
    output        cout      // 输出进位
);

    // 定义内部信号
    wire [15:0] g;          // 进位生成信号
    wire [15:0] p;          // 进位传播信号
    wire [15:0] c;          // 进位信号

    // 计算每个位的进位生成 (G) 和传播 (P)
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : gen_g_p
            assign g[i] = a[i] & b[i];
            assign p[i] = a[i] ^ b[i];
        end
    endgenerate

    // 计算进位信号 (C)
    // C0 = cin
    // C1 = G0 + P0 * C0
    // C2 = G1 + P1 * G0 + P1 * P0 * C0
    // ...
    // C15 = G14 + P14 * G13 + P14 * P13 * G12 + ... + P14 * P13 * ... * P0 * C0

    // 使用生成块计算进位
    generate
        // C0 = cin
        assign c[0] = cin;

        // 对于第i位 (i >= 1)，计算Ci
        for (i = 1; i < 16; i = i + 1) begin : gen_carry
            wire [i-1:0] p_part;
            wire [i-1:0] g_part;

            // 构建从0到i-1的P和G信号
            for (int j = 0; j < i; j = j + 1) begin
                assign p_part[j] = p[j];
                assign g_part[j] = g[j];
            end

            // 计算当前进位
            assign c[i] = g[i-1] | (p[i-1] & c[i-1]);
        end
    endgenerate

    // 计算每一位的和 (S)
    generate
        for (i = 0; i < 16; i = i + 1) begin : gen_sum
            assign sum[i] = p[i] ^ c[i];
        end
    endgenerate

    // 最终的进位输出是C15
    assign cout = c[15];

endmodule