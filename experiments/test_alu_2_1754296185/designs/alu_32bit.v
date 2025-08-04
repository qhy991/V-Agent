
module alu_32bit (
    input [31:0] a,
    input [31:0] b,
    input [3:0] op,
    output [31:0] result,
    output carry_out
);
    assign result = a + b;
    assign carry_out = (a + b > 32'hFFFF_FFFF);
endmodule
