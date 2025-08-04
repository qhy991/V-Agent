module testbench_simple_adder;
  reg a, b;
  wire sum;
  
  // Instantiate the unit under test
  simple_adder uut (.a(a), .b(b), .sum(sum));
  
  // Test sequence
  initial begin
    $display("Testing simple_adder...");
    $monitor("Time=%0t a=%b b=%b sum=%b", $time, a, b, sum);
    
    // Test all combinations
    a = 0; b = 0; #10;
    a = 0; b = 1; #10;
    a = 1; b = 0; #10;
    a = 1; b = 1; #10;
    
    $display("Test completed.");
    $finish;
  end
endmodule