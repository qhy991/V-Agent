`timescale 1ns / 1ps

module tb_alu_8bit;
    
    // Inputs
    reg [7:0] a;
    reg [7:0] b;
    reg [1:0] op;
    
    // Outputs
    wire [7:0] result;
    wire zero;
    
    // Instantiate the Unit Under Test (UUT)
    alu_8bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    initial begin
        $display("Starting ALU 8-bit Testbench");
        
        // Test addition
        a = 8'd10; b = 8'd5; op = 2'b00;
        #10;
        $display("A=%d, B=%d, OP=ADD, Result=%d, Zero=%b", a, b, result, zero);
        
        // Test subtraction
        a = 8'd10; b = 8'd3; op = 2'b01;
        #10;
        $display("A=%d, B=%d, OP=SUB, Result=%d, Zero=%b", a, b, result, zero);
        
        // Test AND operation
        a = 8'b10101010; b = 8'b11110000; op = 2'b10;
        #10;
        $display("A=%b, B=%b, OP=AND, Result=%b, Zero=%b", a, b, result, zero);
        
        // Test OR operation
        a = 8'b10101010; b = 8'b11110000; op = 2'b11;
        #10;
        $display("A=%b, B=%b, OP=OR, Result=%b, Zero=%b", a, b, result, zero);
        
        // Test zero flag
        a = 8'd5; b = 8'd5; op = 2'b01;  // 5-5=0
        #10;
        $display("A=%d, B=%d, OP=SUB, Result=%d, Zero=%b", a, b, result, zero);
        
        // Additional test cases
        a = 8'd0; b = 8'd0; op = 2'b00;  // 0+0=0
        #10;
        $display("A=%d, B=%d, OP=ADD, Result=%d, Zero=%b", a, b, result, zero);
        
        $display("\nTestbench completed");
    end
    
endmodule