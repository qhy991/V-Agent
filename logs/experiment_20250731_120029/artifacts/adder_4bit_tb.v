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

    // Test case 1: Basic addition (0 + 0 = 0)
    a = 4'b0000;
    b = 4'b0000;
    #10;
    $display("Test Case 1: 0 + 0 = %b, Carry = %b", sum, carry);

    // Test case 2: Normal addition (5 + 3 = 8)
    a = 4'b0101;
    b = 4'b0011;
    #10;
    $display("Test Case 2: 5 + 3 = %b, Carry = %b", sum, carry);

    // Test case 3: Boundary value (15 + 0 = 15)
    a = 4'b1111;
    b = 4'b0000;
    #10;
    $display("Test Case 3: 15 + 0 = %b, Carry = %b", sum, carry);

    // Test case 4: Overflow (15 + 1 = 16, carry = 1)
    a = 4'b1111;
    b = 4'b0001;
    #10;
    $display("Test Case 4: 15 + 1 = %b, Carry = %b", sum, carry);

    // Test case 5: Random values (e.g., 7 + 9 = 16, carry = 1)
    a = 4'b0111;
    b = 4'b1001;
    #10;
    $display("Test Case 5: 7 + 9 = %b, Carry = %b", sum, carry);

    // Test case 6: All zeros (0 + 0 = 0)
    a = 4'b0000;
    b = 4'b0000;
    #10;
    $display("Test Case 6: 0 + 0 = %b, Carry = %b", sum, carry);

    // Test case 7: Max value with carry (15 + 1 = 16, carry = 1)
    a = 4'b1111;
    b = 4'b0001;
    #10;
    $display("Test Case 7: 15 + 1 = %b, Carry = %b", sum, carry);

    // Test case 8: Negative numbers (assuming two's complement)
    a = 4'b1000; // -8 in 4-bit two's complement
    b = 4'b1000; // -8 in 4-bit two's complement
    #10;
    $display("Test Case 8: -8 + -8 = %b, Carry = %b", sum, carry);

    // Test case 9: Edge case (15 + 15 = 30, carry = 1)
    a = 4'b1111;
    b = 4'b1111;
    #10;
    $display("Test Case 9: 15 + 15 = %b, Carry = %b", sum, carry);

    // Test case 10: Random test (e.g., 10 + 5 = 15)
    a = 4'b1010;
    b = 4'b0101;
    #10;
    $display("Test Case 10: 10 + 5 = %b, Carry = %b", sum, carry);

    $finish;
  end

endmodule