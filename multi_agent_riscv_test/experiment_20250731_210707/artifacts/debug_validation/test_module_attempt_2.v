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

// riscv_cpu_top.v
// Top-level module for RISC-V CPU core
// This module integrates all the components of the single-cycle RISC-V processor
module riscv_cpu_top (
    input      clk,              // 系统时钟信号
    input      rst_n,            // 异步复位信号（低电平有效）
    input      [31:0] instruction_in,  // 从指令内存读取的32位指令
    input      [31:0] mem_data_in,     // 从数据内存读取的32位数据
    output reg [31:0] pc_out,    // 当前程序计数器值
    output reg [31:0] mem_addr,  // 数据内存地址总线
    output reg [31:0] mem_data_out,  // 要写入数据内存的32位数据
    output reg        mem_write_en,  // 数据内存写使能信号
    output reg        mem_read_en    // 数据内存读使能信号
);

// 内部信号声明
reg [31:0] pc_reg;               // 程序计数器寄存器
reg [31:0] instruction_reg;      // 指令寄存器
reg [31:0] alu_result;           // ALU结果
reg [31:0] regfile_data;         // 寄存器文件数据
reg [31:0] next_pc;              // 下一程序计数器值
reg [31:0] alu_a, alu_b;         // ALU操作数
reg [3:0] alu_op;                // ALU操作码
reg [4:0] rd;                    // 目标寄存器
reg [4:0] rs1, rs2;              // 源寄存器
reg [31:0] imm;                  // 立即数
reg [1:0] opcode;                // 操作码
reg [1:0] funct3;                // 功能字段
reg [6:0] funct7;                // 功能字段
reg [1:0] branch_type;           // 分支类型
reg branch_taken;                // 分支是否被采取
reg [31:0] branch_target;        // 分支目标地址
reg [31:0] data_mem_address;     // 数据内存地址
reg [31:0] data_mem_data;        // 数据内存数据
reg data_mem_write;              // 数据内存写使能
reg data_mem_read;               // 数据内存读使能

// 实例化PC模块
pc_counter pc_inst (
    .clk(clk),
    .rst_n(rst_n),
    .next_pc(next_pc),
    .pc_out(pc_out)
);

// 实例化ALU模块
alu alu_inst (
    .a(alu_a),
    .b(alu_b),
    .alu_op(alu_op),
    .result(alu_result),
    .zero(zero)
);

// 实例化寄存器文件（此处为简化版，实际需要完整实现）
// regfile regfile_inst (
//     .clk(clk),
//     .rst_n(rst_n),
//     .rs1(rs1),
//     .rs2(rs2),
//     .rd(rd),
//     .data_in(regfile_data),
//     .data_out(regfile_data)
// );

// 控制逻辑（此处为简化版，实际需要完整实现）
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc_reg <= 32'h0;
        instruction_reg <= 32'h0;
        next_pc <= 32'h0;
        alu_a <= 32'h0;
        alu_b <= 32'h0;
        alu_op <= 4'b0000;
        rd <= 5'b0;
        rs1 <= 5'b0;
        rs2 <= 5'b0;
        imm <= 32'h0;
        opcode <= 2'b00;
        funct3 <= 2'b00;
        funct7 <= 7'b0000000;
        branch_type <= 2'b00;
        branch_taken <= 1'b0;
        branch_target <= 32'h0;
        data_mem_address <= 32'h0;
        data_mem_data <= 32'h0;
        data_mem_write <= 1'b0;
        data_mem_read <= 1'b0;
    end else begin
        // 这里应包含完整的控制逻辑和数据路径
        // 包括指令解码、寄存器读取、ALU计算、分支判断等
        // 由于篇幅限制，此处仅展示框架
        instruction_reg <= instruction_in;
        
        // 指令解码（示例）
        opcode <= instruction_in[31:30];
        funct3 <= instruction_in[14:12];
        funct7 <= instruction_in[30:25];
        rs1 <= instruction_in[19:15];
        rs2 <= instruction_in[24:20];
        rd <= instruction_in[11:7];
        imm <= instruction_in[31:0];  // 简化处理
        
        // 根据操作码选择ALU操作
        case (opcode)
            2'b01: begin  // I型指令
                alu_op <= funct3;
                alu_a <= regfile_data;  // 假设从寄存器文件读取
                alu_b <= imm;
            end
            2'b11: begin  // S型指令
                alu_op <= 4'b0101;  // SLL
                alu_a <= regfile_data;  // 假设从寄存器文件读取
                alu_b <= imm;
            end
            // 其他操作码处理...
            default: begin
                alu_op <= 4'b0000;
                alu_a <= 32'h0;
                alu_b <= 32'h0;
            end
        endcase
        
        // 分支判断（示例）
        case (opcode)
            2'b11: begin  // B型指令
                // 根据条件判断是否跳转
                // 这里需要完整的条件判断逻辑
                branch_taken <= 1'b0;  // 示例
                branch_target <= pc_out + imm;  // 示例
            end
            default: begin
                branch_taken <= 1'b0;
                branch_target <= 32'h0;
            end
        endcase
        
        // 更新下一PC值
        if (branch_taken) begin
            next_pc <= branch_target;
        end else begin
            next_pc <= pc_out + 4;
        end
        
        // 数据内存访问（示例）
        data_mem_address <= alu_result;  // 示例
        data_mem_data <= regfile_data;   // 示例
        data_mem_write <= 1'b0;          // 示例
        data_mem_read <= 1'b0;           // 示例
    end
end

// 输出端口驱动
assign mem_addr = data_mem_address;
assign mem_data_out = data_mem_data;
assign mem_write_en = data_mem_write;
assign mem_read_en = data_mem_read;

endmodule