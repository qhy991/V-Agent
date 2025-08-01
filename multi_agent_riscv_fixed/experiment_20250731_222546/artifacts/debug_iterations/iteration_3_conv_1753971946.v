module alu_32bit (
    input  [31:0] a,       // 第一个32位操作数
    input  [31:0] b,       // 第二个32位操作数
    input  [3:0]  op,      // 操作码 (4位)
    output reg [31:0] result,  // ALU运算结果
    output reg      zero      // 零标志位，当结果为0时置1
);

    // 定义操作码常量
    localparam OP_ADD = 4'b0000;
    localparam OP_SUB = 4'b0001;
    localparam OP_AND = 4'b0010;
    localparam OP_OR  = 4'b0011;
    localparam OP_XOR = 4'b0100;
    localparam OP_SLL = 4'b0101;  // 左移
    localparam OP_SRL = 4'b0110;  // 右移

    // 根据操作码执行相应的运算
    always @(a, b, op) begin
        case (op)
            OP_ADD: result = a + b;
            OP_SUB: result = a - b;
            OP_AND: result = a & b;
            OP_OR:  result = a | b;
            OP_XOR: result = a ^ b;
            OP_SLL: result = a << b[4:0];  // 使用b的低5位作为移位位数
            OP_SRL: result = a >> b[4:0];  // 使用b的低5位作为移位位数
            default: result = 32'h0;       // 默认情况
        endcase

        // 设置零标志位
        zero = (result == 32'h0) ? 1'b1 : 1'b0;
    end

endmodule