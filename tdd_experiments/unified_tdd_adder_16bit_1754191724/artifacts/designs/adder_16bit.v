module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         cin,
    output reg [15:0] sum,
    output reg        cout,
    output reg        overflow
);

// Perform addition with carry propagation
always @(*) begin
    {cout, sum} = a + b + cin;
    
    // Overflow detection for signed arithmetic:
    // If both operands have the same sign and result has opposite sign → overflow
    overflow = ((a[15] == b[15]) && (a[15] != sum[15]));
end

endmodule