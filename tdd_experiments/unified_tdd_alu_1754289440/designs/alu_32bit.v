module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果
    output        zero      // 零标志 (result == 0 时为1)
);

    // 根据操作码执行相应运算
    always @(*) begin
        case (op)
            4'b0000: result = a + b;     // 加法
            4'b0001: result = a - b;     // 减法
            4'b0010: result = a & b;     // 逻辑与
            4'b0011: result = a | b;     // 逻辑或
            4'b0100: result = a ^ b;     // 异或
            4'b0101: result = a << b[4:0]; // 逻辑左移
            4'b0110: result = a >> b[4:0]; // 逻辑右移
            default: result = 32'h00000000; // 其他操作码
        endcase
    end
    
    // 零标志：当结果为0时输出1
    assign zero = (result == 32'h00000000);
    
endmodule