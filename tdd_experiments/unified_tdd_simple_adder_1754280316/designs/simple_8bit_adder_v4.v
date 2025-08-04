module simple_8bit_adder (
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output [7:0] sum,
    output       cout
);

    // 生成全加器级联
    wire [7:0] carry;
    
    // 第一位全加器
    full_adder fa0 (
        .a(a[0]),
        .b(b[0]),
        .cin(cin),
        .sum(sum[0]),
        .cout(carry[0])
    );
    
    // 其他位全加器
    genvar i;
    for (i = 1; i < 8; i = i + 1) begin : gen_fa
        full_adder fa (
            .a(a[i]),
            .b(b[i]),
            .cin(carry[i-1]),
            .sum(sum[i]),
            .cout(carry[i])
        );
    end
    
    assign cout = carry[7];
    
endmodule