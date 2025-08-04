module alu_32bit(
    input  [31:0] a, b,
    input  [3:0]  op,
    output [31:0] result,
    output       zero
);

    assign result = (op == 4'b0000) ? (a + b) :
                    (op == 4'b0001) ? (a - b) :
                    (op == 4'b0010) ? (a & b) :
                    (op == 4'b0011) ? (a | b) :
                    (op == 4'b0100) ? (a ^ b) :
                    (op == 4'b0101) ? (a << b[4:0]) :
                    (op == 4'b0110) ? (a >> b[4:0]) :
                    (op == 4'b0111) ? ($signed(a) >>> b[4:0]) :
                    32'h0;
    
    assign zero = (result == 32'h0);
    
endmodule