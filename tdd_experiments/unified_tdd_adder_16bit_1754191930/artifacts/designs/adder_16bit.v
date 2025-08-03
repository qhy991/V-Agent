module adder_16bit #(
    parameter WIDTH = 16
) (
    input           clk,
    input           rst,
    input  [WIDTH-1:0] a,
    input  [WIDTH-1:0] b,
    input           cin,
    output reg [WIDTH-1:0] sum,
    output reg      cout,
    output reg      overflow
);

// Internal signals for ripple carry chain
reg [WIDTH-1:0] carry;

// Register the outputs to avoid combinational loops and support clocked behavior
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Compute sum and carry using ripple-carry structure
        carry[0] <= cin;
        for (int i = 0; i < WIDTH - 1; i = i + 1) begin
            carry[i+1] <= (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
        end

        // Calculate sum bits
        for (int i = 0; i < WIDTH; i = i + 1) begin
            sum[i] <= a[i] ^ b[i] ^ carry[i];
        end

        // Output carry is the final carry out
        cout <= carry[WIDTH-1];

        // Overflow detection: signed overflow occurs when two operands of same sign
        // produce a result with opposite sign.
        // For signed addition: overflow = (a_sign == b_sign) && (a_sign != sum_sign)
        overflow <= (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
    end
end

endmodule