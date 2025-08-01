module test_instruction_decoder;
    reg [31:0] instr;
    wire [3:0] alu_op;
    wire [4:0] rs1;
    wire [4:0] rs2;
    wire [4:0] rd;
    wire [31:0] immediate;
    wire mem_read;
    wire mem_write;
    wire reg_write;
    wire branch;

    instruction_decoder uut (
        .instr(instr),
        .alu_op(alu_op),
        .rs1(rs1),
        .rs2(rs2),
        .rd(rd),
        .immediate(immediate),
        .mem_read(mem_read),
        .mem_write(mem_write),
        .reg_write(reg_write),
        .branch(branch)
    );

    initial begin
        // Test R-type instruction (add)
        instr = 32'h00000033;
        #10;
        $display("R-type: alu_op=%b, rs1=%b, rs2=%b, rd=%b, immediate=%b, mem_read=%b, mem_write=%b, reg_write=%b, branch=%b", alu_op, rs1, rs2, rd, immediate, mem_read, mem_write, reg_write, branch);

        // Test I-type instruction (addi)
        instr = 32'h00000013;
        #10;
        $display("I-type: alu_op=%b, rs1=%b, rs2=%b, rd=%b, immediate=%b, mem_read=%b, mem_write=%b, reg_write=%b, branch=%b", alu_op, rs1, rs2, rd, immediate, mem_read, mem_write, reg_write, branch);

        // Test S-type instruction (sw)
        instr = 32'h00000023;
        #10;
        $display("S-type: alu_op=%b, rs1=%b, rs2=%b, rd=%b, immediate=%b, mem_read=%b, mem_write=%b, reg_write=%b, branch=%b", alu_op, rs1, rs2, rd, immediate, mem_read, mem_write, reg_write, branch);

        // Test B-type instruction (beq)
        instr = 32'h00000063;
        #10;
        $display("B-type: alu_op=%b, rs1=%b, rs2=%b, rd=%b, immediate=%b, mem_read=%b, mem_write=%b, reg_write=%b, branch=%b", alu_op, rs1, rs2, rd, immediate, mem_read, mem_write, reg_write, branch);

        $finish;
    end

endmodule