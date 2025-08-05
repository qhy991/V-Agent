module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output reg [31:0] result,   // 修正1: 声明为reg类型
    output reg zero      // 修正2: 声明为reg类型
);

    // 修正3: 声明中间信号
    wire [31:0] add_result;
    wire [31:0] sub_result;
    
    // 修正4: 在always块中给reg类型赋值
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
    
    // 修正5: 移除assign语句，改为在always块中更新zero信号
    always @(*) begin
        zero = (result == 32'h0);
    end

endmodule