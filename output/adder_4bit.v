module adder_4bit (a, b, sum, carry);
  input [3:0] a, b;
  output [3:0] sum;
  output carry;
  
  // 4-bit ripple carry adder
  wire c1, c2, c3;
  
  full_adder fa0 (.a(a[0]), .b(b[0]), .cin(1'b0), .sum(sum[0]), .cout(c1));
  full_adder fa1 (.a(a[1]), .b(b[1]), .cin(c1), .sum(sum[1]), .cout(c2));
  full_adder fa2 (.a(a[2]), .b(b[2]), .cin(c2), .sum(sum[2]), .cout(c3));
  full_adder fa3 (.a(a[3]), .b(b[3]), .cin(c3), .sum(sum[3]), .cout(carry));
endmodule

module full_adder (a, b, cin, sum, cout);
  input a, b, cin;
  output sum, cout;
  
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (b & cin) | (a & cin);
endmodule