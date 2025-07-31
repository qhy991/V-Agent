module full_adder (
    input  a,
    input  b,
    input  cin,
    output sum,
    output cout
);

// Calculate the sum using XOR
assign sum = a ^ b ^ cin;

// Calculate the carry-out using AND and OR gates
assign cout = (a & b) | (a & cin) | (b & cin);

endmodule