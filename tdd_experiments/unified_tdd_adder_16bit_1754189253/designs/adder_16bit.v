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

// Internal signals for intermediate calculations
reg [WIDTH:0] temp_sum;
reg [WIDTH:0] temp_a, temp_b;

// Register to store previous values for overflow detection
reg [WIDTH-1:0] prev_a, prev_b;

always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
        prev_a <= 16'd0;
        prev_b <= 16'd0;
    end else begin
        // Sign-extend inputs to handle signed arithmetic
        temp_a <= {a[WIDTH-1], a};
        temp_b <= {b[WIDTH-1], b};
        
        // Perform addition with carry-in
        temp_sum <= temp_a + temp_b + cin;
        
        // Output sum and carry-out
        sum <= temp_sum[WIDTH-1:0];
        cout <= temp_sum[WIDTH];
        
        // Detect overflow: when both operands have same sign but result has opposite sign
        // Overflow occurs if (a_sign == b_sign) && (a_sign != sum_sign)
        overflow <= (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
        
        // Update previous values for next cycle (if needed for sequential logic)
        prev_a <= a;
        prev_b <= b;
    end
end

endmodule