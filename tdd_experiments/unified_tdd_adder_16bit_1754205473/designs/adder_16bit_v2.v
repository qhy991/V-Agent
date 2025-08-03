module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output [15:0] sum,
    output        cout,
    output        overflow
);

    wire [15:0] internal_sum;
    wire [15:0] carry_out;

    // Generate carry chain using full adders
    assign {carry_out[0], internal_sum[0]} = a[0] + b[0] + cin;
    genvar i;
    generate
        for (i = 1; i < 16; i = i + 1) begin : fa
            assign {carry_out[i], internal_sum[i]} = a[i] + b[i] + carry_out[i-1];
        end
    endgenerate

    assign sum = internal_sum;
    assign cout = carry_out[15];
    assign overflow = (a[15] == b[15]) && (a[15] != internal_sum[15]);

endmodule