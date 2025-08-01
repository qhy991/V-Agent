module alu_32bit (
    input  [31:0] a,       // 第一个32位操作数
    input  [31:0] b,       // 第二个32位操作数  
    input  [3:0]  op,      // 4位操作码
    output reg [31:0] result,  // 32位运算结果
    output reg zero        // 零标志位（结果为0时为1）
);

// 内部信号声明
reg [31:0] add_result;
reg [31:0] sub_result;
reg [31:0] and_result;
reg [31:0] or_result;
reg [31:0] xor_result;
reg [31:0] sll_result;
reg [31:0] srl_result;

// 组合逻辑块：计算所有可能的操作结果并设置零标志位
always @* begin
    // 默认值：无效操作码时的结果
    add_result = 32'h00000000;
    sub_result = 32'h00000000;
    and_result = 32'h00000000;
    or_result = 32'h00000000;
    xor_result = 32'h00000000;
    sll_result = 32'h00000000;
    srl_result = 32'h00000000;

    // 根据操作码计算对应的结果
    case (op)
        4'b0000: begin // OP_ADD
            add_result = a + b;
        end
        4'b0001: begin // OP_SUB
            sub_result = a - b;
        end
        4'b0010: begin // OP_AND
            and_result = a & b;
        end
        4'b0011: begin // OP_OR
            or_result = a | b;
        end
        4'b0100: begin // OP_XOR
            xor_result = a ^ b;
        end
        4'b0101: begin // OP_SLL
            // 使用b的低5位作为移位位数
            sll_result = a << b[4:0];
        end
        4'b0110: begin // OP_SRL
            // 使用b的低5位作为移位位数
            srl_result = a >> b[4:0];
        end
        default: begin // 无效操作码
            // 所有结果都保持为0
        end
    endcase

    // 根据操作码选择正确的结果
    case (op)
        4'b0000: result = add_result;
        4'b0001: result = sub_result;
        4'b0010: result = and_result;
        4'b0011: result = or_result;
        4'b0100: result = xor_result;
        4'b0101: result = sll_result;
        4'b0110: result = srl_result;
        default: result = 32'h00000000; // 无效操作码时输出0
    endcase

    // 计算零标志位
    if (result == 32'h00000000) begin
        zero = 1'b1;
    end else begin
        zero = 1'b0;
    end
end

endmodule