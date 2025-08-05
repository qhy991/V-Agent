module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    // 16位行波进位加法器
    wire [16:0] carry;
    assign carry[0] = cin;
    
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : full_adder_stage
            assign sum[i] = a[i] ^ b[i] ^ carry[i];
            assign carry[i+1] = (a[i] & b[i]) | (carry[i] & (a[i] ^ b[i]));
        end
    endgenerate
    
    assign cout = carry[16];
    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);

endmodule