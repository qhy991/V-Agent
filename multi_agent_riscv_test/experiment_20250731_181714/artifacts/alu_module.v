module alu (input [31:0] a, b, output reg [31:0] result);
  always @(a or b) begin
    result = a + b; // Fixed missing semicolon
  end
endmodule