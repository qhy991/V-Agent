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

    // Test case 1: Basic addition (0 + 0)
    a = 4'b0000;
    b = 4'b0000;
    #10;
    $display("Test Case 1: a=0000, b=0000 -> sum=0000, carry=0");
    if (sum === 4'b0000 && carry === 1'b0) $display("PASS"); else $display("FAIL");

    // Test case 2: Basic addition (1 + 1)
    a = 4'b0001;
    b = 4'b0001;
    #10;
    $display("Test Case 2: a=0001, b=0001 -> sum=0010, carry=0");
    if (sum === 4'b0010 && carry === 1'b0) $display("PASS"); else $display("FAIL");

    // Test case 3: Carry propagation (15 + 1)
    a = 4'b1111;
    b = 4'b0001;
    #10;
    $display("Test Case 3: a=1111, b=0001 -> sum=0000, carry=1");
    if (sum === 4'b0000 && carry === 1'b1) $display("PASS"); else $display("FAIL");

    // Test case 4: Maximum value (15 + 15)
    a = 4'b1111;
    b = 4'b1111;
    #10;
    $display("Test Case 4: a=1111, b=1111 -> sum=1110, carry=1");
    if (sum === 4'b1110 && carry === 1'b1) $display("PASS"); else $display("FAIL");

    // Test case 5: Random values (e.g., 7 + 9)
    a = 4'b0111;
    b = 4'b1001;
    #10;
    $display("Test Case 5: a=0111, b=1001 -> sum=0000, carry=1");
    if (sum === 4'b0000 && carry === 1'b1) $display("PASS"); else $display("FAIL");

    // Test case 6: Edge case (0 + 15)
    a = 4'b0000;
    b = 4'b1111;
    #10;
    $display("Test Case 6: a=0000, b=1111 -> sum=1111, carry=0");
    if (sum === 4'b1111 && carry === 1'b0) $display("PASS"); else $display("FAIL");

    // Test case 7: Edge case (15 + 0)
    a = 4'b1111;
    b = 4'b0000;
    #10;
    $display("Test Case 7: a=1111, b=0000 -> sum=1111, carry=0");
    if (sum === 4'b1111 && carry === 1'b0) $display("PASS"); else $display("FAIL");

    // Test case 8: All ones (15 + 15)
    a = 4'b1111;
    b = 4'b1111;
    #10;
    $display("Test Case 8: a=1111, b=1111 -> sum=1110, carry=1");
    if (sum === 4'b1110 && carry === 1'b1) $display("PASS"); else $display("FAIL");

    // Test case 9: Random values (e.g., 10 + 5)
    a = 4'b1010;
    b = 4'b0101;
    #10;
    $display("Test Case 9: a=1010, b=0101 -> sum=1111, carry=0");
    if (sum === 4'b1111 && carry === 1'b0) $display("PASS"); else $display("FAIL");

    // Test case 10: Random values (e.g., 3 + 12)
    a = 4'b0011;
    b = 4'b1100;
    #10;
    $display("Test Case 10: a=0011, b=1100 -> sum=1111, carry=0");
    if (sum === 4'b1111 && carry === 1'b0) $display("PASS"); else $display("FAIL");

    $finish;
  end
endmodule