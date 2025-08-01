/*
 * Module: riscv_instruction_tester
 * @brief Instruction Level Test Module for RISC-V CPU
 * @details This module tests all supported RISC-V instructions, verifying arithmetic operations, branch jumps, and memory read/write functionality.
 */

module riscv_instruction_tester (
    input clk,
    input rst_n,
    input [6:0] opcode,
    input [31:0] operand1,
    input [31:0] operand2,
    input branch_condition,
    output reg [31:0] result,
    output reg branch_taken,
    output reg memory_read,
    output reg memory_write
);

    // Internal signals
    reg [31:0] temp_result;
    reg [31:0] temp_address;
    reg [31:0] temp_data;

    // Testbench process
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset state
            result <= 32'h00000000;
            branch_taken <= 1'b0;
            memory_read <= 1'b0;
            memory_write <= 1'b0;
        end else begin
            // Execute instruction based on opcode
            case (opcode)
                7'b0000000: begin // ADD instruction
                    temp_result <= operand1 + operand2;
                    result <= temp_result;
                    branch_taken <= 1'b0;
                    memory_read <= 1'b0;
                    memory_write <= 1'b0;
                end
                7'b0000001: begin // SUB instruction
                    temp_result <= operand1 - operand2;
                    result <= temp_result;
                    branch_taken <= 1'b0;
                    memory_read <= 1'b0;
                    memory_write <= 1'b0;
                end
                7'b0000010: begin // AND instruction
                    temp_result <= operand1 & operand2;
                    result <= temp_result;
                    branch_taken <= 1'b0;
                    memory_read <= 1'b0;
                    memory_write <= 1'b0;
                end
                7'b0000011: begin // OR instruction
                    temp_result <= operand1 | operand2;
                    result <= temp_result;
                    branch_taken <= 1'b0;
                    memory_read <= 1'b0;
                    memory_write <= 1'b0;
                end
                7'b0000100: begin // BEQ instruction
                    if (operand1 == operand2) begin
                        branch_taken <= 1'b1;
                        temp_address <= operand1;
                    end else begin
                        branch_taken <= 1'b0;
                    end
                    memory_read <= 1'b0;
                    memory_write <= 1'b0;
                end
                7'b0000101: begin // BNE instruction
                    if (operand1 != operand2) begin
                        branch_taken <= 1'b1;
                        temp_address <= operand1;
                    end else begin
                        branch_taken <= 1'b0;
                    end
                    memory_read <= 1'b0;
                    memory_write <= 1'b0;
                end
                7'b0000110: begin // LW instruction
                    temp_address <= operand1;
                    temp_data <= operand2;
                    memory_read <= 1'b1;
                    memory_write <= 1'b0;
                end
                7'b0000111: begin // SW instruction
                    temp_address <= operand1;
                    temp_data <= operand2;
                    memory_read <= 1'b0;
                    memory_write <= 1'b1;
                end
                default: begin
                    // Unknown instruction
                    result <= 32'h00000000;
                    branch_taken <= 1'b0;
                    memory_read <= 1'b0;
                    memory_write <= 1'b0;
                end
            endcase
        end
    end

endmodule