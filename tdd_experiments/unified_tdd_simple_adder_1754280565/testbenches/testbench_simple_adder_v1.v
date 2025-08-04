`timescale 1ns/1ps

module tb_simple_adder;

  // Testbench signals
  reg clk;
  reg a;
  reg b;
  wire sum;
  
  // Test control signals
  integer i;
  integer test_case;
  integer error_count;
  
  // DUT instantiation
  simple_adder uut (
    .a(a),
    .b(b),
    .sum(sum)
  );
  
  // Clock generation
  always #5 clk = ~clk;
  
  // Initialize simulation
  initial begin
    // Initialize all signals
    clk = 0;
    a = 0;
    b = 0;
    error_count = 0;
    
    // Start waveform dump
    $dumpfile("simple_adder.vcd");
    $dumpvars(0, tb_simple_adder);
    
    // Display start message
    $display("===========================================");
    $display("Starting simple_adder testbench simulation");
    $display("===========================================");
    
    // Run basic test
    test_case = 1;
    $display("Running basic_test...");
    basic_test();
    
    // Run corner test
    test_case = 2;
    $display("Running corner_test...");
    corner_test();
    
    // Display final results
    $display("===========================================");
    $display("Test Results Summary:");
    $display("Total errors detected: %d", error_count);
    if (error_count == 0) begin
      $display("TEST PASSED: All tests completed successfully");
    end else begin
      $display("TEST FAILED: %d errors found", error_count);
    end
    $display("===========================================");
    
    // Finish simulation
    $finish;
  end
  
  // Monitor signals
  initial begin
    $monitor("Time=%0t | Test=%0d | a=%b | b=%b | sum=%b", 
             $time, test_case, a, b, sum);
  end
  
  // Basic functionality test
  task basic_test;
    begin
      // Test all possible input combinations for XOR operation
      a = 0; b = 0; #10;
      if (sum !== 0) begin
        $display("ERROR: Basic test failed at time %0t - Expected sum=0, got sum=%b", $time, sum);
        error_count = error_count + 1;
      end
      
      a = 0; b = 1; #10;
      if (sum !== 1) begin
        $display("ERROR: Basic test failed at time %0t - Expected sum=1, got sum=%b", $time, sum);
        error_count = error_count + 1;
      end
      
      a = 1; b = 0; #10;
      if (sum !== 1) begin
        $display("ERROR: Basic test failed at time %0t - Expected sum=1, got sum=%b", $time, sum);
        error_count = error_count + 1;
      end
      
      a = 1; b = 1; #10;
      if (sum !== 0) begin
        $display("ERROR: Basic test failed at time %0t - Expected sum=0, got sum=%b", $time, sum);
        error_count = error_count + 1;
      end
      
      $display("Basic test completed successfully");
    end
  endtask
  
  // Corner case test
  task corner_test;
    begin
      // Test with random patterns
      for (i = 0; i < 100; i = i + 1) begin
        a = $random % 2;
        b = $random % 2;
        #10;
        
        // Verify XOR operation
        if (sum !== (a ^ b)) begin
          $display("ERROR: Corner test failed at time %0t - a=%b, b=%b, expected sum=%b, got sum=%b", 
                   $time, a, b, (a ^ b), sum);
          error_count = error_count + 1;
        end
      end
      
      // Test boundary conditions with specific values
      a = 0; b = 0; #10;
      if (sum !== 0) begin
        $display("ERROR: Corner test boundary failed at time %0t - Expected sum=0, got sum=%b", $time, sum);
        error_count = error_count + 1;
      end
      
      a = 1; b = 1; #10;
      if (sum !== 0) begin
        $display("ERROR: Corner test boundary failed at time %0t - Expected sum=0, got sum=%b", $time, sum);
        error_count = error_count + 1;
      end
      
      $display("Corner test completed successfully");
    end
  endtask

endmodule