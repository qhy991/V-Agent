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
    wire [15:0] c;          // 中间进位信号

    // 计算每个位的进位生成和传播信号
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : gen_g_p
            assign g[i] = a[i] & b[i];
            assign p[i] = a[i] ^ b[i];
        end
    endgenerate

    // 计算进位信号（超前进位）
    // C0 = cin
    // C1 = G0 + P0*C0
    // C2 = G1 + P1*G0 + P1*P0*C0
    // ...
    // C15 = G14 + P14*G13 + P14*P13*G12 + ... + P14*P13*...*P0*C0

    // 使用递归方式计算进位
    wire [15:0] c_internal;

    // 初始化C0为cin
    assign c_internal[0] = cin;

    // 计算C1到C15
    generate
        for (i = 1; i < 16; i = i + 1) begin : gen_c
            wire [i-1:0] p_part;
            wire [i-1:0] g_part;

            // 提取前i位的p和g
            for (int j = 0; j < i; j = j + 1) begin
                assign p_part[j] = p[j];
                assign g_part[j] = g[j];
            end

            // 计算当前进位
            assign c_internal[i] = g[i-1] | (p[i-1] & c_internal[i-1]);
        end
    endgenerate

    // 计算每个位的和
    generate
        for (i = 0; i < 16; i = i + 1) begin : gen_sum
            assign sum[i] = p[i] ^ c_internal[i];
        end
    endgenerate

    // 最终进位是C15
    assign cout = c_internal[15];

endmodule