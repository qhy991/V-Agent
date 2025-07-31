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

    // Test case 2: Basic addition (1 + 1 = 2)
    a = 4'b0001;
    b = 4'b0001;
    #10;

    // Test case 3: Carry propagation (7 + 1 = 8)
    a = 4'b0111;
    b = 4'b0001;
    #10;

    // Test case 4: Max value (15 + 15 = 30)
    a = 4'b1111;
    b = 4'b1111;
    #10;

    // Test case 5: Min value (0 + 0 = 0)
    a = 4'b0000;
    b = 4'b0000;
    #10;

    // Test case 6: Random values (e.g., 5 + 9 = 14)
    a = 4'b0101;
    b = 4'b1001;
    #10;

    // Test case 7: Overflow (15 + 1 = 16, but 4-bit overflow)
    a = 4'b1111;
    b = 4'b0001;
    #10;

    // Test case 8: All ones with carry-in (15 + 15 + 1 = 31)
    a = 4'b1111;
    b = 4'b1111;
    #10;

    // Test case 9: Edge case (0 + 15 = 15)
    a = 4'b0000;
    b = 4'b1111;
    #10;

    // Test case 10: Edge case (15 + 0 = 15)
    a = 4'b1111;
    b = 4'b0000;
    #10;

    $finish;
  end

  always #5 begin
    $display("Time %0t: a = %b, b = %b, sum = %b, carry = %b", $time, a, b, sum, carry);
  end

endmodule