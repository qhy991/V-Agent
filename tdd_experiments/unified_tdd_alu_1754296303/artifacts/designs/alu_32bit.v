module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果
    output        zero      // 零标志 (result == 0 时为1)
);

    // 操作码定义
    localparam ADD = 4'b0000;
    localparam SUB = 4'b0001;
    localparam AND = 4'b0010;
    localparam OR  = 4'b0011;
    localparam XOR = 4'b0100;
    localparam SLT = 4'b0101;
    localparam SLL = 4'b0110;
    localparam SRL = 4'b0111;
    localparam SRA = 4'b1000;
    
    always @(*) begin
        case (op)
            ADD: result = a + b;
            SUB: result = a - b;
            AND: result = a & b;
            OR:  result = a | b;
            XOR: result = a ^ b;
            SLT: result = (a < b) ? 32'h00000001 : 32'h00000000;
            SLL: result = a << b[4:0];
            SRL: result = a >> b[4:0];
            SRA: result = $signed(a) >>> b[4:0];
            default: result = 32'h00000000;
        endcase
    end
    
    assign zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
    
endmodule