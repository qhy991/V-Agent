module instruction_decoder (
    input [31:0] instr, 
    output reg [3:0] alu_op, 
    output reg [4:0] rs1, 
    output reg [4:0] rs2, 
    output reg [4:0] rd, 
    output reg [31:0] immediate, 
    output reg mem_read, 
    output reg mem_write, 
    output reg reg_write, 
    output reg branch
);

    // 解析指令字段
    always @(instr) begin
        // 提取操作码
        reg [6:0] opcode = instr[6:0];
        
        // 提取功能码
        reg [6:0] funct7 = instr[31:25];
        reg [2:0] funct3 = instr[14:12];
        
        // 提取寄存器地址
        rs1 = instr[24:20];
        rs2 = instr[29:25];
        rd = instr[20:16];
        
        // 根据操作码确定指令类型
        case (opcode)
            7'b0110011: begin // R-type
                alu_op = funct7[5] ? 4'b1000 : 4'b0000; // 示例：根据funct7决定ALU操作
                mem_read = 1'b0;
                mem_write = 1'b0;
                reg_write = 1'b1;
                branch = 1'b0;
                immediate = 32'b0;
            end
            7'b0010011: begin // I-type
                alu_op = 4'b0001; // 示例：加法
                mem_read = 1'b0;
                mem_write = 1'b0;
                reg_write = 1'b1;
                branch = 1'b0;
                immediate = {instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[11:0]}; // 符号扩展
            end
            7'b0100011: begin // S-type
                alu_op = 4'b0010; // 示例：加法
                mem_read = 1'b0;
                mem_write = 1'b1;
                reg_write = 1'b0;
                branch = 1'b0;
                immediate = {instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[11:0]}; // 符号扩展
            end
            7'b1100011: begin // B-type
                alu_op = 4'b0100; // 示例：比较
                mem_read = 1'b0;
                mem_write = 1'b0;
                reg_write = 1'b0;
                branch = 1'b1;
                immediate = {instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[31], instr[11], instr[10], instr[9], instr[8], instr[7], instr[3:0]}; // 符号扩展
            end
            default: begin
                alu_op = 4'b0000;
                mem_read = 1'b0;
                mem_write = 1'b0;
                reg_write = 1'b0;
                branch = 1'b0;
                immediate = 32'b0;
            end
        endcase
    end

endmodule