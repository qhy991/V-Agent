module adder_4bit (a, b, sum, carry);
  input [3:0] a, b;
  output reg [3:0] sum;
  output reg carry;
  reg [4:0] temp_sum;
  always @(a or b) begin
    temp_sum = a + b;
    sum = temp_sum[3:0];
    carry = temp_sum[4];
  end
endmodule