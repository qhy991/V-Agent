// simple_8bit_adder.v
// 8-bit Ripple Carry Adder with Carry-in and Carry-out
// Designed for RTL synthesis, supports basic binary addition

module simple_8bit_adder (
input        clk,        // Clock signal
input        rst,        // Active high reset
input  [7:0] a,         // 8-bit input A
input  [7:0] b,         // 8-bit input B
input        cin,        // Carry-in
output reg [7:0] sum,   // 8-bit sum output
output reg     cout      // Carry-out
);

// Internal signals for intermediate carry values
reg [7:0] carry;

// Sequential logic: register the sum and carry on clock edge
always @(posedge clk or posedge rst) begin
if (rst) begin
sum <= 8'b0;       // Reset sum to 0
cout <= 1'b0;      // Reset carry out to 0
carry <= 8'b0;     // Reset internal carry
end else begin
// Compute each bit of the adder using full adder logic
// Using ripple carry approach
for (integer i = 0; i < 8; i = i + 1) begin
// Full adder for each bit:
// sum[i] = a[i] ^ b[i] ^ carry[i]
// carry[i+1] = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i])
// Note: carry[0] is cin
if (i == 0) begin
sum[i] <= a[i] ^ b[i] ^ cin;
carry[i+1] <= (a[i] & b[i]) | (a[i] & cin) | (b[i] & cin);
end else begin
sum[i] <= a[i] ^ b[i] ^ carry[i];
carry[i+1] <= (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
end
end
// Assign the final carry out
cout <= carry[8];
end
end

endmodule