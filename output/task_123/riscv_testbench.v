`timescale 1ns / 1ps

/**
 * @brief RISC-V CPU Testbench Module
 * @details This module provides a comprehensive test environment for the RISC-V CPU, including instruction memory, data memory, and program execution simulation.
 */

module riscv_testbench (
    input clk,
    input rst_n,
    input [31:0] instruction_addr,
    input [31:0] data_addr,
    input [31:0] data_in,
    output reg [31:0] instruction_out,
    output reg [31:0] data_out,
    output reg [31:0] pc,
    output reg [31:0] regfile
);

    // Internal signals
    reg [31:0] instruction_memory [0:1023];
    reg [31:0] data_memory [0:1023];
    reg [31:0] current_pc;
    reg [31:0] current_instruction;
    reg [31:0] current_data;

    // Initialize instruction and data memory
    initial begin
        // Load test instructions into instruction memory
        // Example: Add two numbers (0x00000001, 0x00000002)
        instruction_memory[0] = 32'h00000001;
        instruction_memory[1] = 32'h00000002;
        // Add instruction (0x00000003)
        instruction_memory[2] = 32'h00000003;
        // Store result (0x00000004)
        instruction_memory[3] = 32'h00000004;
    end

    // Main testbench process
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset state
            current_pc <= 32'h00000000;
            current_instruction <= 32'h00000000;
            current_data <= 32'h00000000;
            instruction_out <= 32'h00000000;
            data_out <= 32'h00000000;
            pc <= 32'h00000000;
            regfile <= 32'h00000000;
        end else begin
            // Fetch instruction from memory
            current_instruction <= instruction_memory[current_pc];
            instruction_out <= current_instruction;
            
            // Execute instruction (simplified example)
            case (current_instruction[31:25])
                7'b0000000: begin // ADD instruction
                    current_data <= current_instruction[24:19] + current_instruction[18:13];
                    regfile <= current_data;
                end
                7'b0000001: begin // STORE instruction
                    data_memory[current_instruction[24:19]] <= current_instruction[18:13];
                    data_out <= data_memory[current_instruction[24:19]];
                end
                default: begin
                    // Unknown instruction
                    current_data <= 32'h00000000;
                end
            endcase
            
            // Update program counter
            current_pc <= current_pc + 32'h00000001;
            pc <= current_pc;
        end
    end

endmodule