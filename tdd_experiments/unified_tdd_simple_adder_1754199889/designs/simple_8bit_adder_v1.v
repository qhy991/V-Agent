module simple_8bit_adder #(
    parameter WIDTH = 8
) (
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input cin,
    output reg [WIDTH-1:0] sum,
    output reg cout
);

// Internal signals for carry propagation
reg [WIDTH-1:0] carry;

// Sequential logic: register outputs on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 8'b0;
        cout <= 1'b0;
    end else begin
        // Initialize first carry bit
        carry[0] <= cin;
        
        // Ripple-carry chain: each stage computes sum and next carry
        for (int i = 0; i < WIDTH; i = i + 1) begin
            // Sum bit is XOR of three inputs: a[i], b[i], carry[i]
            sum[i] <= a[i] ^ b[i] ^ carry[i];
            
            // Carry out is OR of ANDs: (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i])
            // This can be simplified as: (a[i] & b[i]) | (carry[i] & (a[i] | b[i]))
            carry[i+1] <= (a[i] & b[i]) | (carry[i] & (a[i] | b[i]));
        end
        
        // Output carry is the final carry from the most significant bit
        cout <= carry[WIDTH];
    end
end

endmodule