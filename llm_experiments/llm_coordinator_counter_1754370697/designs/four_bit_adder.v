module four_bit_adder (
    input [3:0] a,
    input [3:0] b,
    output [3:0] sum,
    output carry_out
);

    // Internal signal for extended addition
    wire [4:0] result;
    
    // Perform addition with carry
    assign result = a + b;
    assign sum = result[3:0];
    assign carry_out = result[4];
    
endmodule