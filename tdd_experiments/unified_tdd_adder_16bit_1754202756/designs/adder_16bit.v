module adder_16bit #(
    parameter WIDTH = 16
) (
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input cin,
    output reg [WIDTH-1:0] sum,
    output reg cout,
    output reg overflow
);

// Internal signals for carry propagation
reg [WIDTH-1:0] carry;

// Combinational logic for ripple-carry adder
always @(*) begin
    // Initialize carry chain
    carry[0] = cin;
    
    // Ripple-carry adder logic
    for (int i = 0; i < WIDTH; i++) begin
        {carry[i+1], sum[i]} = a[i] + b[i] + carry[i];
    end
    
    // Output carry
    cout = carry[WIDTH];
    
    // Overflow detection for signed arithmetic:
    // Overflow occurs when two positive numbers produce a negative result,
    // or two negative numbers produce a positive result.
    // This is detected by comparing the sign bits of inputs and output.
    overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
end

endmodule