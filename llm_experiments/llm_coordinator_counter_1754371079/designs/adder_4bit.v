module adder_4bit (a, b, sum, carry);
  input [3:0] a, b;
  output [3:0] sum;
  output carry;
  
  reg [4:0] temp_sum;
  
  assign sum = temp_sum[3:0];
  assign carry = temp_sum[4];
  
  always @(*) begin
    temp_sum = a + b;
  end
endmodule