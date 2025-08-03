module adder_16bit #(
    parameter WIDTH = 16
) (
    input               clk,
    input               rst,
    input  [WIDTH-1:0]  a,
    input  [WIDTH-1:0]  b,
    input               cin,
    output reg [WIDTH-1:0] sum,
    output reg          cout,
    output reg          overflow
);

// Internal signals for ripple-carry chain
wire [WIDTH-1:0] carry;

// Generate carry chain using full adders
genvar i;
generate
    // First stage: LSB (i=0)
    assign carry[0] = cin;
    always @(*) begin
        {carry[1], sum[0]} = a[0] + b[0] + carry[0];
    end

    // Remaining stages
    for (i = 1; i < WIDTH; i = i + 1) begin : fa_stage
        always @(*) begin
            {carry[i+1], sum[i]} = a[i] + b[i] + carry[i];
        end
    end
endgenerate

// Final carry out and overflow detection
assign cout = carry[WIDTH];

// Overflow detection for signed addition:
// Overflow occurs when two positive numbers produce a negative result,
// or two negative numbers produce a positive result.
// This is detected by XOR of the last two carry bits (Cin and Cout of MSB).
// For signed arithmetic, overflow = C_out XOR C_{n-1}
assign overflow = carry[WIDTH] ^ carry[WIDTH-1];

// Synchronous register update on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 16'd0;
        cout <= 1'b0;
        overflow <= 1'b0;
    end else begin
        sum <= sum;
        cout <= cout;
        overflow <= overflow;
    end
end

endmodule