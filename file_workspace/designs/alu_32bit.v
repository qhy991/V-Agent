module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果 - 🚨 错误1: 应该是 output reg
    output        zero      // 零标志 - 🚨 错误2: 应该是 output reg
);

    // 🚨 错误3: 中间信号没有声明
    // wire [31:0] add_result;
    // wire [31:0] sub_result;
    
    // 🚨 错误4: always块中给wire类型赋值
    always @(*) begin
        case (op)
            4'b0000: result = a + b;        // ADD
            4'b0001: result = a - b;        // SUB  
            4'b0010: result = a & b;        // AND
            4'b0011: result = a | b;        // OR
            4'b0100: result = a ^ b;        // XOR
            4'b0110: result = a << b[4:0];  // SLL
            4'b0111: result = a >> b[4:0];  // SRL
            default: result = 32'h00000000;
        endcase
    end
    
    // 🚨 错误5: zero信号的assign与always块冲突
    assign zero = (result == 32'h0);

endmodule