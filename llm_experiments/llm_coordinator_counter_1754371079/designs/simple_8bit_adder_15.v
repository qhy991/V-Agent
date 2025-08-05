module simple_8bit_adder(
    input [7:0] a,
    input [7:0] b,
    input cin,
    output [7:0] sum,
    output cout,
    input clk,
    input rst
);

// Internal signals
wire [7:0] g;
wire [7:0] p;
wire [8:0] c;

// Generate carry chain
assign g = a & b;
assign p = a ^ b;
assign c[0] = cin;

genvar i;
generate
    for (i = 0; i < 8; i = i + 1) begin : carry_chain
        assign c[i+1] = g[i] | (p[i] & c[i]);
    end
endgenerate

// Calculate sum
assign sum = p ^ c;

// Output carry out
assign cout = c[8];

endmodule