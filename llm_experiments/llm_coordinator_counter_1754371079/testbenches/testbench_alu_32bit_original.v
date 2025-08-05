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
        
        // 🚨 错误6: task中多语句没有begin..end
        test_add_operation;
        test_sub_operation;
        
        $finish;
    end
    
    // 🚨 错误7: task语法错误 - 多语句需要begin..end
    task test_add_operation;
        a = 32'h12345678;
        b = 32'h87654321;
        op = 4'b0000;
        #10;
        $display("ADD: %h + %h = %h", a, b, result);
    endtask
    
    task test_sub_operation;
        a = 32'hFFFFFFFF;
        b = 32'h00000001;
        op = 4'b0001;
        #10;
        $display("SUB: %h - %h = %h", a, b, result);
    endtask

endmodule