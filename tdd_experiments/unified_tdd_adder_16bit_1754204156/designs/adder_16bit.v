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

// Internal signals for ripple carry chain
reg [WIDTH-1:0] internal_sum;
reg [WIDTH-1:0] carry_out;

// Carry chain logic using full adders
genvar i;
generate
    for (i = 0; i < WIDTH; i = i + 1) begin : fa_chain
        // Full adder at bit i
        if (i == 0) begin
            assign carry_out[0] = cin;
        end else begin
            assign carry_out[i] = (internal_sum[i-1] & carry_out[i-1]) | 
                                 (a[i] & b[i] & carry_out[i-1]) | 
                                 (a[i] & carry_out[i-1] & b[i]) | 
                                 (b[i] & carry_out[i-1] & a[i]);
        end
    end
endgenerate

// Sequential logic for register outputs
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Compute sum and carry out using ripple carry
        internal_sum[0] <= a[0] ^ b[0] ^ cin;
        carry_out[0] <= cin;
        for (int j = 1; j < WIDTH; j = j + 1) begin
            internal_sum[j] <= a[j] ^ b[j] ^ carry_out[j-1];
            carry_out[j] <= (a[j] & b[j]) | (a[j] & carry_out[j-1]) | (b[j] & carry_out[j-1]);
        end
        sum <= internal_sum;
        cout <= carry_out[WIDTH-1];
        
        // Overflow detection for signed addition:
        // Overflow occurs when two operands with same sign produce result with opposite sign.
        // For signed numbers, MSB is the sign bit.
        overflow <= ((a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]));
    end
end

endmodule