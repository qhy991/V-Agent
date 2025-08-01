/*
 * Module Name: riscv_program_tester
 * @brief Program Level Test Module for RISC-V CPU
 * @details This module contains test programs for RISC-V CPU, including Fibonacci sequence calculation, array sorting algorithm, and loop/conditional branch testing.
 */

module riscv_program_tester (
    input clk,
    input rst_n,
    input program_start,
    input [31:0] program_data,
    output reg [31:0] program_result,
    output reg [31:0] execution_cycles,
    output reg [31:0] resource_usage
);

    // Internal signals
    reg [31:0] temp_result;
    reg [31:0] temp_cycle_count;
    reg [31:0] temp_resource_usage;

    // Testbench process
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset state
            program_result <= 32'h00000000;
            execution_cycles <= 32'h00000000;
            resource_usage <= 32'h00000000;
        end else begin
            // Start program execution
            if (program_start) begin
                // Fibonacci sequence calculation
                temp_result <= 32'h00000000;
                temp_cycle_count <= 32'h00000000;
                temp_resource_usage <= 32'h00000000;
                
                // Loop for Fibonacci sequence
                for (int i = 0; i < 10; i++) begin
                    temp_result <= temp_result + program_data;
                    temp_cycle_count <= temp_cycle_count + 32'h00000001;
                    temp_resource_usage <= temp_resource_usage + 32'h00000001;
                end
                
                // Array sorting algorithm
                // Simple bubble sort implementation
                for (int i = 0; i < 5; i++) begin
                    for (int j = 0; j < 5 - i; j++) begin
                        if (program_data[j] > program_data[j+1]) begin
                            temp_result <= program_data[j];
                            program_data[j] <= program_data[j+1];
                            program_data[j+1] <= temp_result;
                        end
                        temp_cycle_count <= temp_cycle_count + 32'h00000001;
                        temp_resource_usage <= temp_resource_usage + 32'h00000001;
                    end
                end
                
                // Loop and conditional branch testing
                if (program_data[0] > 32'h00000005) begin
                    temp_result <= program_data[0] - 32'h00000005;
                end else begin
                    temp_result <= program_data[0] + 32'h00000005;
                end
                
                // Set output values
                program_result <= temp_result;
                execution_cycles <= temp_cycle_count;
                resource_usage <= temp_resource_usage;
            end
        end
    end

endmodule