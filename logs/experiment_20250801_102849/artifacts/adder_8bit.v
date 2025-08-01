module task (
    input  [7:0] a,         // 第一个8位操作数
    input  [7:0] b,         // 第二个8位操作数
    input        cin,       // 输入进位
    output reg [7:0] sum,   // 8位和
    output reg     cout      // 输出进位
);

    // 定义内部信号
    reg [7:0] carry;

    // 第0位全加器
    always @(a or b or cin or carry) begin
        sum[0] = a[0] ^ b[0] ^ cin;
        carry[0] = (a[0] & b[0]) | (a[0] & cin) | (b[0] & cin);
    end

    // 第1位全加器
    always @(a or b or carry[0]) begin
        sum[1] = a[1] ^ b[1] ^ carry[0];
        carry[1] = (a[1] & b[1]) | (a[1] & carry[0]) | (b[1] & carry[0]);
    end

    // 第2位全加器
    always @(a or b or carry[1]) begin
        sum[2] = a[2] ^ b[2] ^ carry[1];
        carry[2] = (a[2] & b[2]) | (a[2] & carry[1]) | (b[2] & carry[1]);
    end

    // 第3位全加器
    always @(a or b or carry[2]) begin
        sum[3] = a[3] ^ b[3] ^ carry[2];
        carry[3] = (a[3] & b[3]) | (a[3] & carry[2]) | (b[3] & carry[2]);
    end

    // 第4位全加器
    always @(a or b or carry[3]) begin
        sum[4] = a[4] ^ b[4] ^ carry[3];
        carry[4] = (a[4] & b[4]) | (a[4] & carry[3]) | (b[4] & carry[3]);
    end

    // 第5位全加器
    always @(a or b or carry[4]) begin
        sum[5] = a[5] ^ b[5] ^ carry[4];
        carry[5] = (a[5] & b[5]) | (a[5] & carry[4]) | (b[5] & carry[4]);
    end

    // 第6位全加器
    always @(a or b or carry[5]) begin
        sum[6] = a[6] ^ b[6] ^ carry[5];
        carry[6] = (a[6] & b[6]) | (a[6] & carry[5]) | (b[6] & carry[5]);
    end

    // 第7位全加器
    always @(a or b or carry[6]) begin
        sum[7] = a[7] ^ b[7] ^ carry[6];
        cout = (a[7] & b[7]) | (a[7] & carry[6]) | (b[7] & carry[6]);
    end

endmodule