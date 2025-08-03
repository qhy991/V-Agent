module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    wire [15:0] carry;
    assign carry[0] = cin;
    assign sum[0] = a[0] ^ b[0] ^ carry[0];
    assign carry[1] = (a[0] & b[0]) | (a[0] & carry[0]) | (b[0] & carry[0]);
    
    genvar i;
    generate
        for (i = 1; i < 16; i = i + 1) begin : carry_chain
            assign sum[i] = a[i] ^ b[i] ^ carry[i];
            assign carry[i+1] = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
        end
    endgenerate

    assign cout = carry[16];
    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);

endmodule