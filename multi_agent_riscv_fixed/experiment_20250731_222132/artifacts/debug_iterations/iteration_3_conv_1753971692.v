module alu (
    input  [31:0] a,      // 第一个32位操作数
    input  [31:0] b,      // 第二个32位操作数
    input  [3:0]  op,     // 操作码 (0000: 加法, 0001: 减法, 0010: 与, 0011: 或, 0100: 异或, 0101: 左移, 0110: 右移)
    output reg [31:0] result  // ALU运算结果输出
);

    // 组合逻辑块，根据op选择不同的运算
    always_comb begin
        case (op)
            4'b0000: result = a + b;       // 加法
            4'b0001: result = a - b;       // 减法
            4'b0010: result = a & b;       // 与
            4'b0011: result = a | b;       // 或
            4'b0100: result = a ^ b;       // 异或
            4'b0101: result = a << b[4:0]; // 左移 (使用b的低5位作为移位次数)
            4'b0110: result = a >> b[4:0]; // 右移 (使用b的低5位作为移位次数)
            default: result = 32'h0;        // 默认情况
        endcase
    end

endmodule