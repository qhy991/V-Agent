module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果
    output        zero      // 零标志 (result == 0 时为1)
);

    // 使用assign语句实现组合逻辑，避免always块语法错误
    assign result = (op == 4'b0000) ? a + b :           // 加法
                   (op == 4'b0001) ? a - b :           // 减法
                   (op == 4'b0010) ? a & b :           // 逻辑与
                   (op == 4'b0011) ? a | b :           // 逻辑或
                   (op == 4'b0100) ? a ^ b :           // 异或
                   (op == 4'b0101) ? a << b[4:0] :     // 逻辑左移
                   (op == 4'b0110) ? a >> b[4:0] :     // 逻辑右移
                   32'b0;                               // 无效操作码输出0

    // 零标志：当结果为0时输出1
    assign zero = (result == 32'b0) ? 1'b1 : 1'b0;

endmodule 