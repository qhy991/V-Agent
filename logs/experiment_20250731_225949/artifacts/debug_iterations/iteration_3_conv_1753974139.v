module alu_32bit (
    input  [31:0] a,       // 第一个32位操作数
    input  [31:0] b,       // 第二个32位操作数  
    input  [3:0]  op,      // 4位操作码
    output [31:0] result,  // 32位运算结果
    output        zero      // 零标志位（结果为0时为1）
);

// 定义操作码常量
localparam OP_ADD = 4'b0000;
localparam OP_SUB = 4'b0001;
localparam OP_AND = 4'b0010;
localparam OP_OR  = 4'b0011;
localparam OP_XOR = 4'b0100;
localparam OP_SLL = 4'b0101;
localparam OP_SRL = 4'b0110;

// 用于移位操作的位数（取b的低5位）
wire [4:0] shift_amount = b[4:0];

// 临时寄存器存储运算结果
reg [31:0] temp_result;

// 根据操作码执行相应的运算
always @* begin
    // 默认值：无效操作码情况
    temp_result = 32'h00000000;
    
    case (op)
        OP_ADD: begin
            temp_result = a + b;
        end
        
        OP_SUB: begin
            temp_result = a - b;
        end
        
        OP_AND: begin
            temp_result = a & b;
        end
        
        OP_OR: begin
            temp_result = a | b;
        end
        
        OP_XOR: begin
            temp_result = a ^ b;
        end
        
        OP_SLL: begin
            // 左移：使用b的低5位作为移位位数
            temp_result = a << shift_amount;
        end
        
        OP_SRL: begin
            // 右移：使用b的低5位作为移位位数
            temp_result = a >> shift_amount;
        end
        
        default: begin
            // 无效操作码，保持默认值
        end
    endcase
end

// 将临时结果赋给输出端口
assign result = temp_result;

// 计算零标志位
assign zero = (temp_result == 32'h00000000) ? 1'b1 : 1'b0;

endmodule