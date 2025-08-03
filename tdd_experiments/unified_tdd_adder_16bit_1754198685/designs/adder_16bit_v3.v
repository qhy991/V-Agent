module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    wire [16:0] temp_sum;
    assign temp_sum = {1'b0, a} + {1'b0, b} + cin;
    assign sum = temp_sum[15:0];
    assign cout = temp_sum[16];
    assign overflow = (a[15] == b[15]) && (a[15] != temp_sum[15]);

endmodule