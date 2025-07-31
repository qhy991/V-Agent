module adder_4bit_tb;

  reg [3:0] a;
  reg [3:0] b;
  wire [3:0] sum;
  wire carry;

  // Instantiate the DUT
  adder_4bit uut (
    .a(a),
    .b(b),
    .sum(sum),
    .carry(carry)
  );

  initial begin
    $dumpfile("adder_4bit_tb.vcd");
    $dumpvars(0, adder_4bit_tb);

    // Test Case 1: Basic Addition (0 + 0)
    a = 4'b0000;
    b = 4'b0000;
    #10;
    $display("Test Case 1: 0 + 0 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 2: Basic Addition (1 + 1)
    a = 4'b0001;
    b = 4'b0001;
    #10;
    $display("Test Case 2: 1 + 1 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 3: Carry Propagation (7 + 1)
    a = 4'b0111;
    b = 4'b0001;
    #10;
    $display("Test Case 3: 7 + 1 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 4: Max Value (15 + 15)
    a = 4'b1111;
    b = 4'b1111;
    #10;
    $display("Test Case 4: 15 + 15 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 5: Random Values
    a = 4'b1010;
    b = 4'b0101;
    #10;
    $display("Test Case 5: 10 + 5 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 6: Edge Case (0 + 15)
    a = 4'b0000;
    b = 4'b1111;
    #10;
    $display("Test Case 6: 0 + 15 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 7: Edge Case (15 + 0)
    a = 4'b1111;
    b = 4'b0000;
    #10;
    $display("Test Case 7: 15 + 0 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 8: Overflow (15 + 1)
    a = 4'b1111;
    b = 4'b0001;
    #10;
    $display("Test Case 8: 15 + 1 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 9: All Ones (15 + 15)
    a = 4'b1111;
    b = 4'b1111;
    #10;
    $display("Test Case 9: 15 + 15 => sum=0x%h, carry=%b", sum, carry);

    // Test Case 10: Random Values
    a = 4'b1100;
    b = 4'b0011;
    #10;
    $display("Test Case 10: 12 + 3 => sum=0x%h, carry=%b", sum, carry);

    // End simulation
    $finish;
  end

endmodule