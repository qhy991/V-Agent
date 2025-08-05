module adder_4bit (
    input wire [3:0] a,
    input wire [3:0] b,
    input wire cin,
    output wire [3:0] sum,
    output wire cout
);

    // 内部信号声明
    wire [3:0] carry;
    
    // 逐位加法器实现
    assign sum[0] = a[0] ^ b[0] ^ cin;
    assign carry[0] = (a[0] & b[0]) | (cin & (a[0] ^ b[0]));
    
    assign sum[1] = a[1] ^ b[1] ^ carry[0];
    assign carry[1] = (a[1] & b[1]) | (carry[0] & (a[1] ^ b[1]));
    
    assign sum[2] = a[2] ^ b[2] ^ carry[1];
    assign carry[2] = (a[2] & b[2]) | (carry[1] & (a[2] ^ b[2]));
    
    assign sum[3] = a[3] ^ b[3] ^ carry[2];
    assign cout = (a[3] & b[3]) | (carry[2] & (a[3] ^ b[3]));
    
endmodule