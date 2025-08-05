`timescale 1ns/1ps

module testbench_alu_32bit;
    reg [31:0] a, b;
    reg [3:0] op;
    wire [31:0] result;
    wire zero;
    
    alu_32bit uut (
        .a(a),
        .b(b), 
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    initial begin
        $display("ALU Test Starting...");
        
        // Fixed: task中多语句添加begin..end
        test_add_operation;
        test_sub_operation;
        
        $finish;
    end
    
    // Fixed: task语法正确 - 添加begin..end块
    task test_add_operation;
        begin
            a = 32'h12345678;
            b = 32'h87654321;
            op = 4'b0000;
            #10;
            $display("ADD: %h + %h = %h", a, b, result);
        end
    endtask
    
    task test_sub_operation;
        begin
            a = 32'hFFFFFFFF;
            b = 32'h00000001;
            op = 4'b0001;
            #10;
            $display("SUB: %h - %h = %h", a, b, result);
        end
    endtask

endmodule