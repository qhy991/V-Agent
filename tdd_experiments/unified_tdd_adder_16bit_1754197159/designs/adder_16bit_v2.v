module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output reg [15:0] sum,
    output reg      cout,
    output reg      overflow
);

    // Internal signals for carry propagation
    wire [15:0] carry;

    // Generate carry chain using full adders
    assign carry[0] = cin;
    generate
        genvar i;
        for (i = 0; i < 16; i = i + 1) begin : fa_inst
            wire c_out;
            wire s_out;
            full_adder fa (
                .a(a[i]),
                .b(b[i]),
                .cin(carry[i]),
                .sum(s_out),
                .cout(c_out)
            );
            assign sum[i] = s_out;
            assign carry[i+1] = c_out;
        end
    endgenerate

    // Output carry
    assign cout = carry[16];

    // Overflow detection: when two same-sign operands produce opposite sign result
    // overflow = (a[15] == b[15]) && (a[15] != sum[15])
    assign overflow = (a[15] == b[15]) && (a[15] != sum[15]);

endmodule