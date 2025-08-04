module adder_4bit(
    input [3:0] a,
    input [3:0] b,
    input cin,
    output [3:0] sum,
    output cout
);

    wire [4:0] temp_sum;
    
    // Full adder for each bit
    assign temp_sum[0] = a[0] ^ b[0] ^ cin;
    assign temp_sum[1] = (a[0] & b[0]) | (cin & (a[0] ^ b[0]));
    assign temp_sum[2] = (a[1] & b[1]) | (temp_sum[1] & (a[1] ^ b[1])) | (a[1] & temp_sum[1]);
    assign temp_sum[3] = (a[2] & b[2]) | (temp_sum[2] & (a[2] ^ b[2])) | (a[2] & temp_sum[2]);
    assign temp_sum[4] = (a[3] & b[3]) | (temp_sum[3] & (a[3] ^ b[3])) | (a[3] & temp_sum[3]);
    
    assign sum = temp_sum[3:0];
    assign cout = temp_sum[4];
    
endmodule