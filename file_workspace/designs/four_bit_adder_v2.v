module four_bit_adder (
    input [3:0] a,
    input [3:0] b,
    input cin,
    output [3:0] sum,
    output cout
);

    // 5-bit vector to hold the result of addition including carry
    wire [4:0] result;
    
    // Perform 4-bit addition with carry-in and carry-out
    assign result = {1'b0, a} + {1'b0, b} + cin;
    
    // Assign outputs
    assign sum = result[3:0];   // 4-bit sum
    assign cout = result[4];    // Carry out

endmodule