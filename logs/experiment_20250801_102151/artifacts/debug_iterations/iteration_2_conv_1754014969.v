module task (
    input  [7:0] a,         // 第一个8位操作数
    input  [7:0] b,         // 第二个8位操作数
    input        cin,       // 输入进位
    output [7:0] sum,       // 8位和
    output       cout       // 输出进位
);

    // 定义内部信号
    wire [7:0] carry;

    // 行波进位链结构
    // 使用连续赋值语句实现全加器逻辑

    // 第一位（LSB）
    assign {carry[0], sum[0]} = a[0] + b[0] + cin;

    // 其他位
    genvar i;
    generate
        for (i = 1; i < 8; i = i + 1) begin : adder_loop
            assign {carry[i], sum[i]} = a[i] + b[i] + carry[i-1];
        end
    endgenerate

    // 最终进位输出
    assign cout = carry[7];

endmodule