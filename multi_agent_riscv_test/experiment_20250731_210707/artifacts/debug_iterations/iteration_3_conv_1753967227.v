// pc_counter.v
// Program Counter module for RISC-V CPU core
// This module implements the program counter functionality for a single-cycle RISC-V processor
module pc_counter (
    input      clk,              // 系统时钟信号
    input      rst_n,            // 异步复位信号（低电平有效）
    input      [31:0] next_pc,   // 下一程序计数器值
    output reg [31:0] pc_out     // 当前程序计数器值
);

// 程序计数器寄存器
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc_out <= 32'h0;        // 复位时清零
    end else begin
        pc_out <= next_pc;      // 正常运行时更新PC
    end
end

endmodule

// alu.v
// Arithmetic Logic Unit module for RISC-V CPU core
// This module implements the arithmetic and logical operations required by the RV32I instruction set
module alu (
    input      [31:0] a,         // 第一个操作数
    input      [31:0] b,         // 第二个操作数
    input      [3:0] alu_op,     // ALU操作码
    output reg [31:0] result,    // ALU结果
    output reg zero              // 零标志
);

// ALU操作定义
// 0000: ADD
// 0001: SUB
// 0010: AND
// 0011: OR
// 0100: XOR
// 0101: SLL
// 0110: SRL
// 0111: SRA
// 1000: SLT
// 1001: SLTU

always @(a, b, alu_op) begin
    case (alu_op)
        4'b0000: result = a + b;
        4'b0001: result = a - b;
        4'b0010: result = a & b;
        4'b0011: result = a | b;
        4'b0100: result = a ^ b;
        4'b0101: result = a << b[4:0];  // SLL
        4'b0110: result = a >> b[4:0];  // SRL
        4'b0111: result = $signed(a) >>> b[4:0];  // SRA
        4'b1000: result = (a < b) ? 1 : 0;  // SLT
        4'b1001: result = (a < b) ? 1 : 0;  // SLTU
        default: result = 32'h0;
    endcase

    // 计算零标志
    zero = (result == 32'h0);
end

endmodule

// regfile.v
// Register File module for RISC-V CPU core
// This module implements the 32x32-bit register file
module regfile (
    input      clk,              // 系统时钟信号
    input      rst_n,            // 异步复位信号（低电平有效）
    input      [4:0] rs1,        // 第一个源寄存器地址
    input      [4:0] rs2,        // 第二个源寄存器地址
    input      [4:0] rd,         // 目标寄存器地址
    input      [31:0] data_in,   // 写入数据
    output reg [31:0] data_out1, // 第一个源寄存器输出
    output reg [31:0] data_out2, // 第二个源寄存器输出
    output reg [31:0] regfile_data // 用于ALU的寄存器数据
);

// 寄存器文件存储
reg [31:0] registers [0:31]; // 32个32位寄存器

// 读取寄存器
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        data_out1 <= 32'h0;
        data_out2 <= 32'h0;
        regfile_data <= 32'h0;
    end else begin
        data_out1 <= registers[rs1];
        data_out2 <= registers[rs2];
        regfile_data <= registers[rd]; // 用于ALU的寄存器数据
    end
end

// 写入寄存器
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 复位时清零所有寄存器
        integer i;
        for (i = 0; i < 32; i = i + 1) begin
            registers[i] <= 32'h0;
        end
    end else begin
        // 只有当rd不是0时才写入
        if (rd != 5'b0) begin
            registers[rd] <= data_in;
        end
    end
end

endmodule

// ifu.v
// Instruction Fetch Unit module for RISC-V CPU core
// This module implements the instruction fetch functionality
module ifu (
    input      clk,              // 系统时钟信号
    input      rst_n,            // 异步复位信号（低电平有效）
    input      [31:0] pc_in,     // 程序计数器输入
    output reg [31:0] instruction_out,  // 指令输出
    output reg [31:0] pc_out     // 程序计数器输出
);

// 指令内存（简化为寄存器）
reg [31:0] instruction_mem [0:1023]; // 假设指令内存大小为1KB

// 指令获取逻辑
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc_out <= 32'h0;
        instruction_out <= 32'h0;
    end else begin
        // 从指令内存读取指令
        instruction_out <= instruction_mem[pc_in[31:2]]; // 假设4字节对齐
        
        // 更新程序计数器
        pc_out <= pc_in + 4;
    end
end

endmodule

// idu.v
// Instruction Decode Unit module for RISC-V CPU core
// This module implements the instruction decode functionality
module idu (
    input      [31:0] instruction_in,  // 指令输入
    output reg [4:0] rs1,        // 第一个源寄存器地址
    output reg [4:0] rs2,        // 第二个源寄存器地址
    output reg [4:0] rd,         // 目标寄存器地址
    output reg [31:0] imm,        // 立即数
    output reg [1:0] opcode,     // 操作码
    output reg [2:0] funct3,     // 功能字段
    output reg [6:0] funct7,     // 功能字段
    output reg [1:0] branch_type // 分支类型
);

// 指令解码逻辑
always @(instruction_in) begin
    opcode <= instruction_in[31:30];
    funct3 <= instruction_in[14:12];
    funct7 <= instruction_in[30:25];
    rs1 <= instruction_in[19:15];
    rs2 <= instruction_in[24:20];
    rd <= instruction_in[11:7];
    
    // 根据操作码提取立即数
    case (opcode)
        2'b00: begin // R型指令
            imm <= 32'h0;
        end
        2'b01: begin // I型指令
            imm <= {{20{instruction_in[31]}}, instruction_in[31:20]};
        end
        2'b10: begin // S型指令
            imm <= {{20{instruction_in[31]}}, instruction_in[31:25], instruction_in[11:7]};
        end
        2'b11: begin // B型指令
            imm <= {{20{instruction_in[31]}}, instruction_in[7], instruction_in[30:25], instruction_in[11:8], 1'b0};
        end
        default: begin
            imm <= 32'h0;
        end
    endcase
    
    // 设置分支类型
    case (opcode)
        2'b11: begin // B型指令
            branch_type <= 2'b00; // BEQ
            if (funct3 == 3'b000) branch_type <= 2'b00; // BEQ
            else if (funct3 == 3'b001) branch_type <= 2'b01; // BNE
            else if (funct3 == 3'b100) branch_type <= 2'b10; // BLT
            else if (funct3 == 3'b101) branch_type <= 2'b11; // BGE
        end
        default: begin
            branch_type <= 2'b00;
        end
    endcase
end

endmodule