
module alu_32bit (
    input [31:0] a,
    input [31:0] b,
    input [3:0] op,
    output [31:0] result,
    output zero
);
    assign result = a + b;
    assign zero = (result == 0);
endmodule
