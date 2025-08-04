module simple_8bit_adder (
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output [7:0] sum,
    output       cout
);

    // 8位全加器实现
    assign {cout, sum} = a + b + cin;
    
endmodule