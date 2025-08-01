module alu(input [31:0] a, b, output reg [31:0] result);
  always @(a, b) begin
    result = a + b; // Missing semicolon here
  end
endmodule