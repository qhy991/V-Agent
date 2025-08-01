// Description: Program Counter (PC) module for RISC-V CPU core
// This module implements the program counter functionality for a single-cycle RISC-V processor
module pc_counter (
    input clk,              // 系统时钟信号
    input rst_n,            // 异步复位信号（低电平有效）
    input [31:0] branch_addr, // 分支目标地址
    input branch_valid,     // 分支有效信号
    output reg [31:0] pc_out // 当前程序计数器值，连接到指令内存地址
);

// 内部寄存器
reg [31:0] pc_reg;

// 主要逻辑：在时钟上升沿更新PC
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc_reg <= 32'h0;  // 复位时PC为0
    end else begin
        if (branch_valid) begin
            pc_reg <= branch_addr;  // 如果有分支有效，则跳转到目标地址
        end else begin
            pc_reg <= pc_reg + 32'h4;  // 否则PC递增4
        end
    end
end

endmodule

// Description: Arithmetic Logic Unit (ALU) module for RISC-V CPU core
// This module implements the ALU functionality for a single-cycle RISC-V processor
module alu (
    input [31:0] a,          // 第一个操作数
    input [31:0] b,          // 第二个操作数
    input [3:0] alu_control,  // ALU控制信号
    output reg [31:0] result, // ALU运算结果
    output reg zero_flag      // 零标志位
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

always @(a, b, alu_control) begin
    case (alu_control)
        4'b0000: result = a + b;
        4'b0001: result = a - b;
        4'b0010: result = a & b;
        4'b0011: result = a | b;
        4'b0100: result = a ^ b;
        4'b0101: result = a << b[4:0];  // SLL
        4'b0110: result = a >> b[4:0];  // SRL
        4'b0111: result = $signed(a) >> b[4:0];  // SRA
        4'b1000: result = (a < b) ? 1 : 0;  // SLT
        4'b1001: result = (a < b) ? 1 : 0;  // SLTU
        default: result = 32'h0;
    endcase
    
    // 计算零标志
    zero_flag = (result == 32'h0) ? 1 : 0;
end

endmodule

// Description: Register File module for RISC-V CPU core
// This module implements a 32x32-bit register file
module register_file (
    input clk,
    input rst_n,
    input [4:0] read_reg1,
    input [4:0] read_reg2,
    input [4:0] write_reg,
    input [31:0] write_data,
    input write_enable,
    output reg [31:0] read_data1,
    output reg [31:0] read_data2
);

// 寄存器文件存储
reg [31:0] regs[31:0];  // 32个寄存器

// 读取寄存器
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        read_data1 <= 32'h0;
        read_data2 <= 32'h0;
    end else begin
        read_data1 <= regs[read_reg1];
        read_data2 <= regs[read_reg2];
    end
end

// 写入寄存器
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 复位时所有寄存器清零
        integer i;
        for (i = 0; i < 32; i = i + 1) begin
            regs[i] <= 32'h0;
        end
    end else if (write_enable) begin
        regs[write_reg] <= write_data;
    end
end

endmodule

// Description: Instruction Decode Unit (IDU) for RISC-V CPU core
// This module decodes instructions and generates control signals
module idu (
    input clk,
    input rst_n,
    input [31:0] instruction,
    input [31:0] regfile_read_data1,
    input [31:0] regfile_read_data2,
    input [31:0] alu_result,
    input zero_flag,
    output reg [31:0] branch_addr,
    output reg branch_valid,
    output reg [31:0] mem_addr,
    output reg [31:0] mem_data_out,
    output reg mem_write_en,
    output reg mem_read_en,
    output reg [4:0] rs1,
    output reg [4:0] rs2,
    output reg [4:0] rd,
    output reg [3:0] alu_control,
    output reg write_enable
);

// 指令解码逻辑
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 初始化所有输出
        branch_addr <= 32'h0;
        branch_valid <= 1'b0;
        mem_addr <= 32'h0;
        mem_data_out <= 32'h0;
        mem_write_en <= 1'b0;
        mem_read_en <= 1'b0;
        rs1 <= 5'h0;
        rs2 <= 5'h0;
        rd <= 5'h0;
        alu_control <= 4'h0;
        write_enable <= 1'b0;
    end else begin
        // 解码指令
        case (instruction[6:0])  // 取出操作码
            7'b0110011: begin  // R-type
                rs1 <= instruction[19:15];
                rs2 <= instruction[24:20];
                rd <= instruction[11:7];
                alu_control <= instruction[31:25];  // ALU控制信号
                write_enable <= 1'b1;
                branch_valid <= 1'b0;
            end
            7'b0010011: begin  // I-type (ADDI, ANDI, ORI)
                rs1 <= instruction[19:15];
                rd <= instruction[11:7];
                alu_control <= instruction[31:25];  // ALU控制信号
                write_enable <= 1'b1;
                branch_valid <= 1'b0;
            end
            7'b1100011: begin  // B-type (BEQ, BNE, BLT, BGE)
                rs1 <= instruction[19:15];
                rs2 <= instruction[24:20];
                branch_addr <= pc_value + {instruction[31], instruction[30:25], instruction[11:1], 1'b0};
                branch_valid <= 1'b1;
            end
            7'b0000011: begin  // I-type (LW)
                rs1 <= instruction[19:15];
                rd <= instruction[11:7];
                alu_control <= 4'b0000;  // ADD
                write_enable <= 1'b1;
                mem_addr <= regfile_read_data1 + instruction[31:16];  // 计算有效地址
                mem_read_en <= 1'b1;
            end
            7'b0100011: begin  // S-type (SW)
                rs1 <= instruction[19:15];
                rs2 <= instruction[24:20];
                alu_control <= 4'b0000;  // ADD
                mem_addr <= regfile_read_data1 + instruction[31:16];  // 计算有效地址
                mem_data_out <= regfile_read_data2;
                mem_write_en <= 1'b1;
            end
            default: begin
                // 其他指令处理
                branch_valid <= 1'b0;
                write_enable <= 1'b0;
            end
        endcase
    end
end

endmodule

// Description: Memory Interface Unit for RISC-V CPU core
// This module handles memory access operations
module memory_interface (
    input clk,
    input rst_n,
    input [31:0] mem_addr,
    input [31:0] mem_data_in,
    output reg [31:0] mem_data_out,
    output reg mem_write_en,
    output reg mem_read_en,
    input [31:0] regfile_write_data
);

// 内存接口逻辑
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        mem_data_out <= 32'h0;
        mem_write_en <= 1'b0;
        mem_read_en <= 1'b0;
    end else begin
        // 这里可以添加实际的内存访问逻辑
        // 本示例中仅模拟内存读写
        if (mem_read_en) begin
            mem_data_out <= mem_data_in;  // 从内存读取数据
        end
        if (mem_write_en) begin
            // 写入内存（此处仅为示例）
        end
    end
end

endmodule

// Description: Top-level RISC-V CPU core module
// This module integrates all the components of a single-cycle RISC-V processor
module riscv_cpu_top (
    input clk,              // 系统时钟信号
    input rst_n,            // 异步复位信号（低电平有效）
    input [31:0] instruction_in,  // 从指令内存读取的32位指令
    input [31:0] mem_data_in,     // 从数据内存读取的32位数据
    output reg [31:0] pc_out,     // 当前程序计数器值，连接到指令内存地址
    output reg [31:0] mem_addr,   // 数据内存地址总线
    output reg [31:0] mem_data_out,  // 要写入数据内存的32位数据
    output reg mem_write_en,      // 数据内存写使能信号
    output reg mem_read_en        // 数据内存读使能信号
);

// 内部信号声明
wire [31:0] pc_value;
wire [31:0] instr;
wire [31:0] regfile_read_data1;
wire [31:0] regfile_read_data2;
wire [31:0] alu_result;
wire zero_flag;
wire [31:0] branch_addr;
wire branch_valid;

// 实例化PC模块
pc_counter pc_inst (
    .clk(clk),
    .rst_n(rst_n),
    .branch_addr(branch_addr),
    .branch_valid(branch_valid),
    .pc_out(pc_value)
);

// 实例化指令译码单元 (IDU)
idu idu_inst (
    .clk(clk),
    .rst_n(rst_n),
    .instruction(instruction_in),
    .regfile_read_data1(regfile_read_data1),
    .regfile_read_data2(regfile_read_data2),
    .alu_result(alu_result),
    .zero_flag(zero_flag),
    .branch_addr(branch_addr),
    .branch_valid(branch_valid),
    .mem_addr(mem_addr),
    .mem_data_out(mem_data_out),
    .mem_write_en(mem_write_en),
    .mem_read_en(mem_read_en),
    .rs1(rs1),
    .rs2(rs2),
    .rd(rd),
    .alu_control(alu_control),
    .write_enable(write_enable)
);

// 实例化ALU模块
alu alu_inst (
    .a(regfile_read_data1),
    .b(regfile_read_data2),
    .alu_control(idu_inst.alu_control),
    .result(alu_result),
    .zero_flag(zero_flag)
);

// 实例化寄存器文件 (Register File)
register_file regfile_inst (
    .clk(clk),
    .rst_n(rst_n),
    .read_reg1(idu_inst.rs1),
    .read_reg2(idu_inst.rs2),
    .write_reg(idu_inst.rd),
    .write_data(alu_result),
    .write_enable(idu_inst.write_enable),
    .read_data1(regfile_read_data1),
    .read_data2(regfile_read_data2)
);

// 实例化内存接口单元 (Memory Interface Unit)
memory_interface mem_intf_inst (
    .clk(clk),
    .rst_n(rst_n),
    .mem_addr(mem_addr),
    .mem_data_in(mem_data_in),
    .mem_data_out(mem_data_out),
    .mem_write_en(mem_write_en),
    .mem_read_en(mem_read_en),
    .regfile_write_data(regfile_read_data1)  // 假设LW指令需要将数据写入寄存器
);

endmodule