// AND gate module: simple_and_gate
// Module type: simple_gate
module simple_and_gate (
    input  a,
    input  b,
    output y
);

// 实现逻辑与运算
assign y = a & b;

endmodule