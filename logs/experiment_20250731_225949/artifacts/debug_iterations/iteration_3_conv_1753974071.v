module alu_32bit (
    input  [31:0] a,       // 第一个32位操作数
    input  [31:0] b,       // 第二个32位操作数  
    input  [3:0]  op,      // 4位操作码
    output [31:0] result,  // 32位运算结果
    output        zero     // 零标志位（结果为0时为1）
);

    // 定义操作码常量
    localparam OP_ADD = 4'b0000;
    localparam OP_SUB = 4'b0001;
    localparam OP_AND = 4'b0010;
    localparam OP_OR  = 4'b0011;
    localparam OP_XOR = 4'b0100;
    localparam OP_SLL = 4'b0101;
    localparam OP_SRL = 4'b0110;

    // 定义中间结果信号
    reg [31:0] result_reg;

    // 计算零标志位
    assign zero = (result_reg == 32'h0) ? 1'b1 : 1'b0;

    // 组合逻辑实现
    always @(*) begin
        case (op)
            OP_ADD: result_reg = a + b;
            OP_SUB: result_reg = a - b;
            OP_AND: result_reg = a & b;
            OP_OR:  result_reg = a | b;
            OP_XOR: result_reg = a ^ b;
            OP_SLL: result_reg = a << b[4:0];  // 使用b的低5位作为移位位数
            OP_SRL: result_reg = a >> b[4:0];  // 使用b的低5位作为移位位数
            default: result_reg = 32'h0;       // 无效操作码，输出0
        endcase
    end

    // 将结果寄存器连接到输出端口
    assign result = result_reg;

endmodule