// RISC-V CPU Testbench
`timescale 1ns / 1ps

module riscv_cpu_testbench();

// Clock and reset signals
reg clk;
reg rst_n;

// Instruction memory (IMEM)
reg [31:0] imem [0:1023];

// Data memory (DMEM)
reg [31:0] dmem [0:1023];

// CPU interface signals
wire [31:0] pc;
wire [31:0] instr;
wire [31:0] alu_result;
wire [31:0] regfile_out;

// Instantiate the RISC-V CPU module
riscv_cpu cpu(
    .clk(clk),
    .rst_n(rst_n),
    .pc(pc),
    .instr(instr),
    .alu_result(alu_result),
    .regfile_out(regfile_out)
);

// Initialize the testbench
initial begin
    // Set initial values
    clk = 0;
    rst_n = 0;
    #10 rst_n = 1;

    // Load instructions into instruction memory
    // Example: Load a simple program to compute Fibonacci sequence
    imem[0] = 32'h00000000; // NOP
    imem[1] = 32'h00000000; // NOP
    imem[2] = 32'h00000000; // NOP
    imem[3] = 32'h00000000; // NOP
    imem[4] = 32'h00000000; // NOP
    imem[5] = 32'h00000000; // NOP
    imem[6] = 32'h00000000; // NOP
    imem[7] = 32'h00000000; // NOP
    imem[8] = 32'h00000000; // NOP
    imem[9] = 32'h00000000; // NOP
    
    // Add more instructions as needed for the test program

    // Run the simulation for a certain number of cycles
    #1000 $finish;
end

// Monitor the CPU output
always @(posedge clk) begin
    $display("PC: %h, Instruction: %h, ALU Result: %h, Register File Output: %h", pc, instr, alu_result, regfile_out);
end

endmodule