# 修复后的完整RISC-V CPU设计

## 问题分析

从错误信息来看，主要问题是：

1. `timescale` 指令被错误地放在模块定义之前
2. 模块定义中存在语法错误（如缺少分号）
3. 代码中存在未完成的模块实例化（ALU模块未完成）
4. 顶层模块 `riscv_cpu.v` 的代码不完整，导致编译失败

## 修复后的完整代码

```verilog
// pc_counter.v
/*
 * pc_counter.v
 *
 * Program Counter (PC) module for a simplified 32-bit RISC-V processor core.
 * This module implements the program counter functionality with support for:
 * - Incrementing by 4 on normal execution
 * - Branching to target addresses
 * - Jumping to target addresses
 * - Reset functionality
 *
 * Parameters:
 *   WIDTH - Width of the data bus (32 bits)
 *
 * Input Ports:
 *   clk - System clock signal
 *   rst_n - Asynchronous reset signal (active low)
 *   branch_target - Target address for branch instructions
 *   jump_target - Target address for jump instructions
 *   pc_in - Next PC value from instruction memory (for jumps)
 *
 * Output Ports:
 *   pc_out - Current program counter value
 */

`timescale 1ns / 1ps

module pc_counter #(
    parameter WIDTH = 32
)(
    // Clock and reset
    input wire clk,
    input wire rst_n,

    // Control signals
    input wire is_branch,
    input wire is_jump,

    // Address inputs
    input wire [WIDTH-1:0] branch_target,
    input wire [WIDTH-1:0] jump_target,
    input wire [WIDTH-1:0] pc_in,

    // Output
    output reg [WIDTH-1:0] pc_out
);

// Local parameters
localparam OFFSET = 4; // Instruction size in bytes

// Main logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc_out <= 32'h0;
    end else begin
        if (is_branch || is_jump) begin
            // Branch or jump instruction: use target address
            pc_out <= (is_branch) ? branch_target : jump_target;
        end else begin
            // Normal execution: increment by 4
            pc_out <= pc_in + OFFSET;
        end
    end
end

endmodule
```

```verilog
// alu.v
/*
 * alu.v
 *
 * Arithmetic Logic Unit (ALU) for a simplified 32-bit RISC-V processor core.
 * This module implements basic arithmetic and logical operations including:
 * - ADD, SUB, AND, OR, XOR
 * - SLL, SRL, SRA
 * - Comparison operations for branch instructions
 *
 * Parameters:
 *   WIDTH - Width of the data bus (32 bits)
 *
 * Input Ports:
 *   a - First operand
 *   b - Second operand
 *   alu_op - ALU operation code
 *   is_shift - Indicates if this is a shift operation
 *   is_compare - Indicates if this is a comparison operation
 *
 * Output Ports:
 *   result - Result of the ALU operation
 *   zero_flag - Zero flag (1 if result is zero)
 */

`timescale 1ns / 1ps

module alu #(
    parameter WIDTH = 32
)(
    // Inputs
    input wire [WIDTH-1:0] a,
    input wire [WIDTH-1:0] b,
    input wire [3:0] alu_op,
    input wire is_shift,
    input wire is_compare,

    // Outputs
    output reg [WIDTH-1:0] result,
    output reg zero_flag
);

// Local parameters
localparam OP_ADD = 4'b0000;
localparam OP_SUB = 4'b0001;
localparam OP_AND = 4'b0010;
localparam OP_OR  = 4'b0011;
localparam OP_XOR = 4'b0100;
localparam OP_SLL = 4'b0101;
localparam OP_SRL = 4'b0110;
localparam OP_SRA = 4'b0111;
localparam OP_SLT = 4'b1000;
localparam OP_SLTU = 4'b1001;

// Main logic
always @(a or b or alu_op or is_shift or is_compare) begin
    case (alu_op)
        OP_ADD: result = a + b;
        OP_SUB: result = a - b;
        OP_AND: result = a & b;
        OP_OR: result = a | b;
        OP_XOR: result = a ^ b;
        OP_SLL: result = a << b[4:0]; // Shift amount is lower 5 bits
        OP_SRL: result = a >> b[4:0]; // Logical right shift
        OP_SRA: result = $signed(a) >>> b[4:0]; // Arithmetic right shift
        OP_SLT: result = ($signed(a) < $signed(b)) ? 1 : 0;
        OP_SLTU: result = (a < b) ? 1 : 0;
        default: result = 32'h0;
    endcase

    // Set zero flag
    zero_flag = (result == 32'h0) ? 1 : 0;
end

endmodule
```

```verilog
// riscv_cpu.v
/*
 * riscv_cpu.v
 *
 * Complete 32-bit RISC-V processor core implementing RV32I instruction set.
 * This module integrates all key components of the processor including:
 * - Program Counter (PC)
 * - Instruction Fetch Unit (IFU)
 * - Instruction Decode Unit (IDU)
 * - Arithmetic Logic Unit (ALU)
 * - Register File
 * - Memory Interface Unit
 *
 * Parameters:
 *   WIDTH - Width of the data bus (32 bits)
 *
 * Input Ports:
 *   clk - System clock signal
 *   rst_n - Asynchronous reset signal (active low)
 *   instruction_in - 32-bit instruction from instruction memory
 *   mem_data_in - 32-bit data from data memory
 *
 * Output Ports:
 *   pc_out - Current program counter value
 *   mem_addr - Data memory address
 *   mem_data_out - Data to be written to data memory
 *   mem_write_en - Data memory write enable
 *   mem_read_en - Data memory read enable
 */

`timescale 1ns / 1ps

module riscv_cpu #(
    parameter WIDTH = 32
)(
    // Clock and reset
    input wire clk,
    input wire rst_n,

    // Instruction and data interface
    input wire [WIDTH-1:0] instruction_in,
    input wire [WIDTH-1:0] mem_data_in,

    // Memory interface
    output reg [WIDTH-1:0] pc_out,
    output reg [WIDTH-1:0] mem_addr,
    output reg [WIDTH-1:0] mem_data_out,
    output reg mem_write_en,
    output reg mem_read_en
);

// Local parameters
localparam INSTR_SIZE = 4; // Instruction size in bytes

// Internal signals
reg [WIDTH-1:0] pc_value;
reg [WIDTH-1:0] instr_reg;
reg [WIDTH-1:0] reg_file [0:31]; // 32x32-bit register file
reg [WIDTH-1:0] alu_result;
reg [WIDTH-1:0] alu_operand_a;
reg [WIDTH-1:0] alu_operand_b;
reg [WIDTH-1:0] next_pc;
reg [3:0] alu_op;
reg is_branch;
reg is_jump;
reg is_load;
reg is_store;
reg is_alu;
reg is_imm;
reg is_rtype;
reg is_jal;
reg is_jalr;
reg is_btype;
reg is_itype;
reg is_stype;
reg is_utype;
reg is_ujtype;
reg is_lui;
reg is_auipc;
reg is_call;
reg is_return;
reg [4:0] rd;
reg [4:0] rs1;
reg [4:0] rs2;
reg [11:0] imm;
reg [31:0] pc_next;
reg [31:0] pc_current;
reg [31:0] pc_next_branch;
reg [31:0] pc_next_jump;
reg [31:0] pc_next_normal;
reg [31:0] pc_next_call;
reg [31:0] pc_next_return;
reg [31:0] pc_next_other;

// Instantiate modules
pc_counter pc_counter_inst (
    .clk(clk),
    .rst_n(rst_n),
    .is_branch(is_branch),
    .is_jump(is_jump),
    .branch_target(pc_next_branch),
    .jump_target(pc_next_jump),
    .pc_in(pc_next_normal),
    .pc_out(pc_value)
);

// ALU instance
alu alu_inst (
    .a(alu_operand_a),
    .b(alu_operand_b),
    .alu_op(alu_op),
    .is_shift(1'b0), // Not used in this implementation
    .is_compare(1'b0), // Not used in this implementation
    .result(alu_result),
    .zero_flag()
);

// Instruction decode unit (simplified)
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        instr_reg <= 32'h0;
        pc_current <= 32'h0;
        pc_next_normal <= 32'h0;
        pc_next_branch <= 32'h0;
        pc_next_jump <= 32'h0;
        pc_next_call <= 32'h0;
        pc_next_return <= 32'h0;
        pc_next_other <= 32'h0;
        alu_op <= 4'h0;
        is_branch <= 1'b0;
        is_jump <= 1'b0;
        is_load <= 1'b0;
        is_store <= 1'b0;
        is_alu <= 1'b0;
        is_imm <= 1'b0;
        is_rtype <= 1'b0;
        is_jal <= 1'b0;
        is_jalr <= 1'b0;
        is_btype <= 1'b0;
        is_itype <= 1'b0;
        is_stype <= 1'b0;
        is_utype <= 1'b0;
        is_ujtype <= 1'b0;
        is_lui <= 1'b0;
        is_auipc <= 1'b0;
        is_call <= 1'b0;
        is_return <= 1'b0;
        rd <= 5'h0;
        rs1 <= 5'h0;
        rs2 <= 5'h0;
        imm <= 12'h0;
    end else begin
        // Instruction decoding
        instr_reg <= instruction_in;
        
        // Extract opcode
        reg [6:0] opcode = instruction_in[6:0];
        
        // Determine instruction type
        is_rtype = (opcode == 7'h33); // R-type
        is_itype = (opcode == 7'h01 || opcode == 7'h03 || opcode == 7'h13 || opcode == 7'h1B); // I-type
        is_stype = (opcode == 7'h23); // S-type
        is_btype = (opcode == 7'h02 || opcode == 7'h0A || opcode == 7'h0B); // B-type
        is_utype = (opcode == 7'h0F || opcode == 7'h17); // U-type
        is_ujtype = (opcode == 7'h1F); // UJ-type
        is_jal = (opcode == 7'h6F); // JAL
        is_jalr = (opcode == 7'h67); // JALR
        is_call = (opcode == 7'h6F && instruction_in[11:7] == 5'h0); // CALL
        is_return = (opcode == 7'h67 && instruction_in[11:7] == 5'h0); // RETURN
        
        // Extract operands
        if (is_rtype) begin
            rs1 <= instruction_in[19:15];
            rs2 <= instruction_in[24:20];
            rd <= instruction_in[11:7];
            alu_op <= instruction_in[31:25]; // ALU operation code
            is_alu <= 1'b1;
            is_imm <= 1'b0;
            is_load <= 1'b0;
            is_store <= 1'b0;
        end else if (is_itype) begin
            rs1 <= instruction_in[19:15];
            rd <= instruction_in[11:7];
            imm <= instruction_in[31:20]; // Immediate value
            is_imm <= 1'b1;
            is_alu <= 1'b1;
            is_load <= 1'b0;
            is_store <= 1'b0;
            
            // Determine specific I-type instruction
            if (instruction_in[31:25] == 6'h0) begin // ADDI
                alu_op <= 4'h0;
            end else if (instruction_in[31:25] == 6'h4) begin // ANDI
                alu_op <= 4'h2;
            end else if (instruction_in[31:25] == 6'h5) begin // ORI
                alu_op <= 4'h3;
            end else if (instruction_in[31:25] == 6'h6) begin // XORI
                alu_op <= 4'h4;
            end else if (instruction_in[31:25] == 6'h7) begin // SLLI
                alu_op <= 4'h5;
            end else if (instruction_in[31:25] == 6'h8) begin // SLTI
                alu_op <= 4'h8;
            end else if (instruction_in[31:25] == 6'h9) begin // SLTIU
                alu_op <= 4'h9;
            end else if (instruction_in[31:25] == 6'h10) begin // SRLI
                alu_op <= 4'h6;
            end else if (instruction_in[31:25] == 6'h18) begin // SRAI
                alu_op <= 4'h7;
            end
        end else if (is_stype) begin
            rs1 <= instruction_in[19:15];
            rs2 <= instruction_in[24:20];
            imm <= {instruction_in[31:25], instruction_in[11:7]}; // Immediate value
            is_store <= 1'b1;
            is_imm <= 1'b1;
            is_alu <= 1'b0;
        end else if (is_btype) begin
            rs1 <= instruction_in[19:15];
            rs2 <= instruction_in[24:20];
            imm <= {instruction_in[31], instruction_in[30:25], instruction_in[11:7], 1'b0}; // Branch offset
            is_branch <= 1'b1;
            is_imm <= 1'b1;
            is_alu <= 1'b0;
        end else if (is_utype) begin
            rd <= instruction_in[11:7];
            imm <= {instruction_in[31:12], 12'h0}; // U-type immediate
            is_imm <= 1'b1;
            is_alu <= 1'b0;
        end else if (is_ujtype) begin
            rd <= instruction_in[11:7];
            imm <= {instruction_in[31], instruction_in[30:20], instruction_in[11], 1'b0}; // UJ-type immediate
            is_jump <= 1'b1;
            is_imm <= 1'b1;
            is_alu <= 1'b0;
        end else if (is_jal) begin
            rd <= instruction_in[11:7];
            imm <= {instruction_in[31], instruction_in[30:20], instruction_in[11], 1'b0}; // JAL immediate
            is_jump <= 1'b1;
            is_imm <= 1'b1;
            is_alu <= 1'b0;
        end else if (is_jalr) begin
            rs1 <= instruction_in[19:15];
            rd <= instruction_in[11:7];
            imm <= instruction_in[31:20]; // JALR immediate
            is_jump <= 1'b1;
            is_imm <= 1'b1;
            is_alu <= 1'b0;
        end
        
        // Calculate next PC values
        pc_next_normal <= pc_value + INSTR_SIZE;
        
        if (is_branch) begin
            // Branch instruction: calculate target address
            pc_next_branch <= pc_value + imm;
        end
        
        if (is_jump) begin
            // Jump instruction: calculate target address
            pc_next_jump <= pc_value + imm;
        end
        
        // For calls and returns
        if (is_call) begin
            pc_next_call <= pc_value + INSTR_SIZE;
        end
        
        if (is_return) begin
            pc_next_return <= pc_value + INSTR_SIZE;
        end
        
        // Default next PC value
        pc_next_other <= pc_value + INSTR_SIZE;
        
        // Select next PC value based on instruction type
        if (is_branch) begin
            pc_next <= pc_next_branch;
        end else if (is_jump) begin
            pc_next <= pc_next_jump;
        end else if (is_call) begin
            pc_next <= pc_next_call;
        end else if (is_return) begin
            pc_next <= pc_next_return;
        end else begin
            pc_next <= pc_next_other;
        end
        
        // Update current PC
        pc_current <= pc_next;
        
        //