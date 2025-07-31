module testbench;
  reg [3:0] a, b;
  wire [3:0] sum;
  wire carry;
  
  // Instantiate the 4-bit adder
  adder_4bit uut (.a(a), .b(b), .sum(sum), .carry(carry));
  
  initial begin
    // Test case 1: 0 + 0 = 0
    a = 4'b0000; b = 4'b0000; #10;
    
    // Test case 2: 5 + 3 = 8
    a = 4'b0101; b = 4'b0011; #10;
    
    // Test case 3: 15 + 1 = 16 (overflow)
    a = 4'b1111; b = 4'b0001; #10;
    
    // Test case 4: 7 + 8 = 15
    a = 4'b0111; b = 4'b1000; #10;
    
    $finish;
  end
endmodule