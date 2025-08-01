module alu_32bit (
    input  [31:0] a,       // 第一个32位操作数
    input  [31:0] b,       // 第二个32位操作数  
    input  [3:0]  op,      // 4位操作码
    output wire [31:0] result,  // 32位运算结果
    output wire zero        // 零标志位（结果为0时为1）
);

// 定义操作码常量
localparam OP_ADD = 4'b0000;
localparam OP_SUB = 4'b0001;
localparam OP_AND = 4'b0010;
localparam OP_OR  = 4'b0011;
localparam OP_XOR = 4'b0100;
localparam OP_SLL = 4'b0101;
localparam OP_SRL = 4'b0110;

// 定义中间信号
reg [31:0] add_result;
reg [31:0] sub_result;
reg [31:0] and_result;
reg [31:0] or_result;
reg [31:0] xor_result;
reg [31:0] sll_result;
reg [31:0] srl_result;

// 组合逻辑块
always_comb begin
    // 默认值：无效操作码时输出0
    result = 32'h00000000;
    zero = 1'b1;

    // 根据操作码选择运算
    case (op)
        OP_ADD: begin
            add_result = a + b;
            result = add_result;
            zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
        end
        
        OP_SUB: begin
            sub_result = a - b;
            result = sub_result;
            zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
        end
        
        OP_AND: begin
            and_result = a & b;
            result = and_result;
            zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
        end
        
        OP_OR: begin
            or_result = a | b;
            result = or_result;
            zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
        end
        
        OP_XOR: begin
            xor_result = a ^ b;
            result = xor_result;
            zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
        end
        
        OP_SLL: begin
            // 使用b的低5位作为移位位数
            sll_result = a << b[4:0];
            result = sll_result;
            zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
        end
        
        OP_SRL: begin
            // 使用b的低5位作为移位位数
            srl_result = a >> b[4:0];
            result = srl_result;
            zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
        end
        
        default: begin
            // 无效操作码，保持默认值
        end
    endcase
end

// 输出信号驱动
assign result = (op == OP_ADD) ? add_result :
                (op == OP_SUB) ? sub_result :
                (op == OP_AND) ? and_result :
                (op == OP_OR) ? or_result :
                (op == OP_XOR) ? xor_result :
                (op == OP_SLL) ? sll_result :
                (op == OP_SRL) ? srl_result :
                32'h00000000;

assign zero = (result == 32'h00000000) ? 1'b1 : 1'b0;

endmodule