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

// 用于移位的位数（取b的低5位）
wire [4:0] shift_amount = b[4:0];

// 定义中间结果寄存器
reg [31:0] result_reg;

// 根据操作码执行相应的运算
always @* begin
    case (op)
        OP_ADD: begin
            result_reg = a + b;
        end
        
        OP_SUB: begin
            result_reg = a - b;
        end
        
        OP_AND: begin
            result_reg = a & b;
        end
        
        OP_OR: begin
            result_reg = a | b;
        end
        
        OP_XOR: begin
            result_reg = a ^ b;
        end
        
        OP_SLL: begin
            result_reg = a << shift_amount;
        end
        
        OP_SRL: begin
            result_reg = a >> shift_amount;
        end
        
        default: begin
            result_reg = 32'h00000000;
        end
    endcase
end

// 将结果输出到外部
assign result = result_reg;

// 计算零标志位
assign zero = (result_reg == 32'h00000000);

endmodule