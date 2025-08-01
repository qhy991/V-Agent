output y;

assign y = a & b;

// AND gate module: simple_and_gate
// Module type: simple_gate
module simple_and_gate (
    input  a,
    input  b,
    output wire y
);

// 实现逻辑与运算
assign y = a & b;

endmodule

module testbench;

    reg a, b;
    wire y;

    // 实例化 AND 门
    simple_and_gate uut (
        .a(a),
        .b(b),
        .y(y)
    );

    initial begin
        $monitor("a = %b, b = %b, y = %b", a, b, y);

        // 测试所有输入组合
        a = 0; b = 0; #10;
        a = 0; b = 1; #10;
        a = 1; b = 0; #10;
        a = 1; b = 1; #10;

        $finish;
    end

endmodule