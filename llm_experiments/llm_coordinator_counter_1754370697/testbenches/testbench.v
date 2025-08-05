`timescale 1ns/1ps

module testbench;

  // Testbench signals
  reg clk;
  reg rst_n;
  reg [31:0] a, b;
  reg [3:0] opcode;
  wire [31:0] result;
  wire zero;
  
  // Instantiate the ALU
  alu uut (
    .clk(clk),
    .rst_n(rst_n),
    .a(a),
    .b(b),
    .opcode(opcode),
    .result(result),
    .zero(zero)
  );
  
  // Clock generation
  always #5 clk = ~clk;
  
  // Test sequence
  initial begin
    // Initialize signals
    clk = 0;
    rst_n = 0;
    a = 0;
    b = 0;
    opcode = 0;
    
    // Reset sequence
    #10 rst_n = 1;
    
    // Test tasks with multiple statements
    test_operation(5, 3, 4);
    #10;
    test_operation(10, 7, 1);
    #10;
    
    $finish;
  end
  
  // Task with multiple statements (this will cause the error)
  task test_operation;
    input [31:0] val_a, val_b;
    input [3:0] op;
    begin
      a = val_a;
      b = val_b;
      opcode = op;
      #10; // Wait for computation
      $display("Operation %b: %d + %d = %d", op, val_a, val_b, result);
    end
  endtask
  
endmodule