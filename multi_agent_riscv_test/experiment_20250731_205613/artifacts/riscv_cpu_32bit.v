/*
 * Module: pc_counter
 * Description: Program Counter module for RISC-V CPU core
 * Features:
 *   - 32-bit program counter
 *   - Supports instruction fetching and branch prediction
 *   - Handles PC increment and branch target calculation
 *   - Includes reset functionality
 * Parameters:
 *   WIDTH - Width of the program counter (32 bits)
 */

`timescale 1ns / 1ps

module pc_counter #(
    parameter WIDTH = 32
)(
    // Clock and reset
    input wire clk,
    input wire rst_n,

    // Instruction memory interface
    input wire [WIDTH-1:0] instruction_in,

    // Control signals
    input wire [WIDTH-1:0] branch_target,
    input wire branch_taken,

    // Output to instruction memory
    output reg [WIDTH-1:0] pc_out
);

// Internal signal declarations
reg [WIDTH-1:0] pc_reg;

// Reset logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc_reg <= 32'h0;
    end else begin
        if (branch_taken) begin
            pc_reg <= branch_target;
        end else begin
            pc_reg <= pc_reg + 4; // Increment by 4 bytes for 32-bit instructions
        end
    end
end

// Output assignment
assign pc_out = pc_reg;

endmodule

/*
 * Module: alu
 * Description: Arithmetic Logic Unit for RISC-V CPU core
 * Features:
 *   - Supports RV32I integer operations
 *   - Includes ALU control for various operations
 *   - Handles data forwarding
 * Parameters:
 *   WIDTH - Width of the ALU operands and result (32 bits)
 */

`timescale 1ns / 1ps

module alu #(
    parameter WIDTH = 32
)(
    // Input operands
    input wire [WIDTH-1:0] a,
    input wire [WIDTH-1:0] b,

    // ALU operation control
    input wire [3:0] alu_op,

    // Data forwarding inputs
    input wire [WIDTH-1:0] forward_a,
    input wire [WIDTH-1:0] forward_b,
    input wire forward_a_valid,
    input wire forward_b_valid,

    // Output result
    output reg [WIDTH-1:0] result,

    // Flags (not used in this simplified version)
    output reg zero_flag
);

// Internal signal declarations
wire [WIDTH-1:0] a_input;
wire [WIDTH-1:0] b_input;

// Select between original operands and forwarded values
assign a_input = (forward_a_valid) ? forward_a : a;
assign b_input = (forward_b_valid) ? forward_b : b;

// ALU operation implementation
always @(a_input, b_input, alu_op) begin
    case (alu_op)
        4'b0000: result = a_input + b_input; // ADD
        4'b0001: result = a_input - b_input; // SUB
        4'b0010: result = a_input & b_input; // AND
        4'b0011: result = a_input | b_input; // OR
        4'b0100: result = a_input ^ b_input; // XOR
        4'b0101: result = a_input << b_input[4:0]; // SLL
        4'b0110: result = a_input >> b_input[4:0]; // SRL
        4'b0111: result = $signed(a_input) >>> b_input[4:0]; // SRA
        default: result = 32'h0; // Default case
    endcase

    // Zero flag calculation
    zero_flag = (result == 32'h0);
end

endmodule