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

// Sequential logic: register outputs on rising edge of clock
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 8'b0;
        cout <= 1'b0;
        carry <= 1'b0;
    end else begin
        // Initialize first carry bit
        carry[0] <= cin;
        
        // Ripple-carry adder logic: each bit computes sum and carry
        // Bit 0 to 7
        for (int i = 0; i < WIDTH; i++) begin
            // Sum = a[i] XOR b[i] XOR carry[i]
            sum[i] <= a[i] ^ b[i] ^ carry[i];
            // Carry out = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i])
            carry[i+1] <= (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
        end
        
        // Output carry is the final carry from the most significant bit
        cout <= carry[WIDTH];
    end
end

endmodule