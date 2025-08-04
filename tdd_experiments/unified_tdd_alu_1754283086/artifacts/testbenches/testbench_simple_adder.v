`timescale 1ns/1ps

module tb_simple_adder;

  // Testbench signals
  reg a;
  reg b;
  wire sum;
  
  // Simulation control signals
  reg clk;
  reg reset_n;
  integer i;
  integer test_case;
  
  // DUT instantiation
  simple_adder uut (
    .a(a),
    .b(b),
    .sum(sum)
  );
  
  // Clock generation
  always #5.0 clk = ~clk;
  
  // Test case execution
  initial begin
    // Initialize signals
    a = 0;
    b = 0;
    clk = 0;
    reset_n = 1;
    
    // Start simulation
    $display("Starting simple_adder testbench at time %0t", $time);
    $dumpfile("simple_adder.vcd");
    $dumpvars(0, tb_simple_adder);
    
    // Run basic test
    test_case = 1;
    $display("Running basic_test at time %0t", $time);
    basic_test();
    
    // Run boundary test
    test_case = 2;
    $display("Running boundary_test at time %0t", $time);
    boundary_test();
    
    // Finish simulation
    $display("Testbench completed at time %0t", $time);
    $finish;
  end
  
  // Monitor for signal changes
  initial begin
    $monitor("Time %0t: a=%b, b=%b, sum=%b", $time, a, b, sum);
  end
  
  // Basic functionality test
  task basic_test;
    begin
      // Test all combinations of inputs
      for (i = 0; i < 4; i = i + 1) begin
        a = i[1];
        b = i[0];
        #10;
        if (sum !== (a + b)) begin
          $display("ERROR: Basic test failed at time %0t. Expected sum=%b, got sum=%b", $time, (a + b), sum);
        end else begin
          $display("PASS: Basic test - a=%b, b=%b, sum=%b", a, b, sum);
        end
      end
    end
  endtask
  
  // Boundary condition test
  task boundary_test;
    begin
      // Test boundary values
      a = 0;
      b = 0;
      #10;
      if (sum !== 0) begin
        $display("ERROR: Boundary test failed - zero inputs should give zero output");
      end else begin
        $display("PASS: Boundary test - zero inputs");
      end
      
      a = 1;
      b = 0;
      #10;
      if (sum !== 1) begin
        $display("ERROR: Boundary test failed - one input should give one output");
      end else begin
        $display("PASS: Boundary test - one input");
      end
      
      a = 0;
      b = 1;
      #10;
      if (sum !== 1) begin
        $display("ERROR: Boundary test failed - one input should give one output");
      end else begin
        $display("PASS: Boundary test - one input");
      end
      
      a = 1;
      b = 1;
      #10;
      if (sum !== 2) begin
        $display("ERROR: Boundary test failed - one plus one should give two");
      end else begin
        $display("PASS: Boundary test - one plus one");
      end
    end
  endtask

endmodule