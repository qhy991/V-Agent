module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output reg [15:0] sum,
    output reg        cout,
    output reg        overflow
);

always @(*) begin
    // 计算和与进位（行波进位）
    reg [16:0] temp_sum;
    reg [16:0] carry;
    
    carry[0] = cin;
    for (int i = 0; i < 16; i = i + 1) begin
        temp_sum[i] = a[i] ^ b[i] ^ carry[i];
        carry[i+1] = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
    end
    
    sum = temp_sum[15:0];
    cout = carry[16];
    
    // 溢出检测：同号相加结果异号则溢出
    // sign_a = a[15], sign_b = b[15], sign_sum = sum[15]
    overflow = (a[15] == b[15]) && (a[15] != sum[15]);
end

endmodule