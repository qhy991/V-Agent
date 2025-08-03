module adder_16bit #(
    parameter WIDTH = 16
) (
    input           clk,
    input           rst,
    input  [WIDTH-1:0] a,
    input  [WIDTH-1:0] b,
    input             cin,
    output reg [WIDTH-1:0] sum,
    output reg        cout,
    output reg        overflow
);

// Internal signals for carry propagation
reg [WIDTH:0] carry;

// Combinational logic for addition and overflow detection
always @(*) begin
    // Initialize outputs
    carry[0] = cin;
    
    // Ripple-carry adder implementation
    for (int i = 0; i < WIDTH; i = i + 1) begin
        carry[i+1] = (a[i] & b[i] & carry[i]) | 
                     (a[i] & ~b[i] & ~carry[i]) | 
                     (~a[i] & b[i] & ~carry[i]) | 
                     (~a[i] & ~b[i] & carry[i]);
    end
    
    // Compute sum and output carry
    sum = a ^ b ^ carry[WIDTH:1];
    cout = carry[WIDTH];
    
    // Overflow detection for signed numbers:
    // Overflow occurs when two operands with same sign produce result with opposite sign
    // i.e., (a[15] == b[15]) && (a[15] != sum[15])
    overflow = (a[15] == b[15]) && (a[15] != sum[15]);
end

// Synchronous register update on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= {WIDTH{1'b0}};
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Outputs are updated synchronously based on combinational logic
        // The combinational logic drives the values, which are registered here
        // This ensures proper timing and avoids combinational loops
        sum <= sum;
        cout <= cout;
        overflow <= overflow;
    end
end

endmodule