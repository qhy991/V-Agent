module alu_32bit (
    input [31:0] a,
    input [31:0] b,
    input [3:0] op,
    output [31:0] result,
    output zero
);

    wire [31:0] add_result;
    wire [31:0] sub_result;
    wire [31:0] and_result;
    wire [31:0] or_result;
    wire [31:0] xor_result;
    wire [31:0] shl_result;
    wire [31:0] shr_result;
    
    // 加法运算
    assign add_result = a + b;
    
    // 减法运算
    assign sub_result = a - b;
    
    // 逻辑与运算
    assign and_result = a & b;
    
    // 逻辑或运算
    assign or_result = a | b;
    
    // 异或运算
    assign xor_result = a ^ b;
    
    // 逻辑左移运算 (使用b的低5位作为移位量)
    assign shl_result = a << b[4:0];
    
    // 逻辑右移运算 (使用b的低5位作为移位量)
    assign shr_result = a >> b[4:0];
    
    // 根据操作码选择结果
    always @(*) begin
        case (op)
            4'b0000: result = add_result;   // 加法
            4'b0001: result = sub_result;   // 减法
            4'b0010: result = and_result;   // 逻辑与
            4'b0011: result = or_result;    // 逻辑或
            4'b0100: result = xor_result;   // 异或
            4'b0101: result = shl_result;   // 左移
            4'b0110: result = shr_result;   // 右移
            default: result = 32'b0;         // 无效操作码
        endcase
    end
    
    // 零标志：当结果为0时输出1
    assign zero = (result == 32'b0) ? 1'b1 : 1'b0;

endmodule