// pc_counter.v - Program Counter module for RISC-V CPU core
module pc_counter (
    input clk,              // 系统时钟信号
    input rst_n,            // 异步复位信号（低电平有效）
    input [31:0] branch_addr, // 分支目标地址
    input branch_valid,     // 分支有效信号
    output reg [31:0] pc_out // 当前程序计数器值，连接到指令内存地址
);

    // 内部寄存器存储当前PC值
    reg [31:0] pc_reg;

    // 初始化PC值为0
    initial begin
        pc_reg = 32'h0;
    end

    // 主要逻辑：在时钟上升沿更新PC值
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_reg <= 32'h0;  // 复位时清零
        end else begin
            if (branch_valid) begin
                pc_reg <= branch_addr;  // 如果有分支有效，则跳转到目标地址
            end else begin
                pc_reg <= pc_reg + 32'h4;  // 否则顺序执行下一条指令
            end
        end
    end

    // 将内部寄存器输出到pc_out端口
    // 注意：这里直接驱动output reg，而不是使用assign语句
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_out <= 32'h0;
        end else begin
            pc_out <= pc_reg;
        end
    end

endmodule

// alu.v - Arithmetic Logic Unit for RISC-V CPU core
module alu (
    input [31:0] a,          // 第一个操作数
    input [31:0] b,          // 第二个操作数
    input [3:0] alu_op,      // ALU操作码
    output reg [31:0] result // ALU运算结果
);

    // 根据不同的操作码执行相应的运算
    always @(*) begin
        case (alu_op)
            4'b0000: result = a + b;           // ADD
            4'b0001: result = a - b;           // SUB
            4'b0010: result = a & b;           // AND
            4'b0011: result = a | b;           // OR
            4'b0100: result = a ^ b;           // XOR
            4'b0101: result = a << b[4:0];     // SLL
            4'b0110: result = a >> b[4:0];     // SRL
            4'b0111: result = $signed(a) >>> b[4:0]; // SRA
            default: result = 32'h0;           // 默认情况
        endcase
    end

endmodule

// riscv_cpu_top.v - Top-level module for RISC-V CPU core
module riscv_cpu_top (
    input clk,              // 系统时钟信号
    input rst_n,            // 异步复位信号（低电平有效）
    input [31:0] instruction_in,  // 从指令内存读取的32位指令
    input [31:0] mem_data_in,     // 从数据内存读取的32位数据
    output reg [31:0] pc_out,       // 当前程序计数器值，连接到指令内存地址
    output reg [31:0] mem_addr,     // 数据内存地址总线
    output reg [31:0] mem_data_out, // 要写入数据内存的32位数据
    output reg mem_write_en,        // 数据内存写使能信号
    output reg mem_read_en,         // 数据内存读使能信号
    output reg [31:0] reg_file_wdata, // 写入寄存器文件的数据
    output reg [4:0] reg_file_waddr, // 写入寄存器文件的地址
    output reg reg_file_we,         // 寄存器文件写使能信号
    output reg [31:0] alu_result,   // ALU运算结果
    output reg [31:0] branch_target // 分支目标地址
);

    // 内部信号声明
    reg [31:0] pc_value;
    reg [31:0] instruction;
    reg [31:0] alu_result_internal;
    reg [31:0] reg_file_wdata_internal;
    reg [4:0] reg_file_waddr_internal;
    reg reg_file_we_internal;
    reg [31:0] mem_addr_internal;
    reg [31:0] mem_data_out_internal;
    reg mem_write_en_internal;
    reg mem_read_en_internal;
    reg [31:0] branch_target_internal;

    // 实例化Program Counter模块
    pc_counter pc_inst (
        .clk(clk),
        .rst_n(rst_n),
        .branch_addr(branch_target_internal),
        .branch_valid(mem_read_en_internal),  // 假设读操作表示分支有效
        .pc_out(pc_value)
    );

    // 实例化ALU模块
    alu alu_inst (
        .a(instruction[25:0]),  // 假设a是立即数部分
        .b(reg_file_wdata_internal),  // 假设b是寄存器文件数据
        .alu_op(instruction[31:28]),  // 假设操作码在高位
        .result(alu_result_internal)
    );

    // 这里需要添加完整的指令解码、执行等逻辑
    // 由于篇幅限制，这里仅展示基本结构

    // 输出信号驱动
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_out <= 32'h0;
            mem_addr <= 32'h0;
            mem_data_out <= 32'h0;
            mem_write_en <= 1'b0;
            mem_read_en <= 1'b0;
            reg_file_wdata <= 32'h0;
            reg_file_waddr <= 5'h0;
            reg_file_we <= 1'b0;
            alu_result <= 32'h0;
            branch_target <= 32'h0;
        end else begin
            pc_out <= pc_value;
            mem_addr <= mem_addr_internal;
            mem_data_out <= mem_data_out_internal;
            mem_write_en <= mem_write_en_internal;
            mem_read_en <= mem_read_en_internal;
            reg_file_wdata <= reg_file_wdata_internal;
            reg_file_waddr <= reg_file_waddr_internal;
            reg_file_we <= reg_file_we_internal;
            alu_result <= alu_result_internal;
            branch_target <= branch_target_internal;
        end
    end

endmodule