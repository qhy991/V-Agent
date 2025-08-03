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
reg [WIDTH-1:0] c;

// Sequential logic: register outputs on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 8'd0;
        cout <= 1'b0;
    end else begin
        // Initialize first carry bit
        c[0] <= cin;
        
        // Ripple-carry adder logic: compute each bit sum and propagate carry
        for (int i = 0; i < WIDTH; i = i + 1) begin
            // Sum bit is XOR of three inputs: a[i], b[i], and incoming carry
            sum[i] <= a[i] ^ b[i] ^ c[i];
            
            // Carry out is OR of ANDs: (a[i] & b[i]) | (a[i] & c[i]) | (b[i] & c[i])
            // This can be simplified as: (a[i] & b[i]) | (c[i] & (a[i] | b[i]))
            c[i+1] <= (a[i] & b[i]) | (c[i] & (a[i] | b[i]));
        end
        
        // Output carry is the final carry from the most significant bit
        cout <= c[WIDTH];
    end
end

endmodule