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

// Internal signals for ripple-carry adder
wire [WIDTH-1:0] carry;

// Generate carry chain using full adders
genvar i;
generate
    // First full adder (least significant bit)
    assign carry[0] = cin;
    always @(*) begin
        {carry[1], sum[0]} = a[0] + b[0] + carry[0];
    end

    // Remaining full adders
    for (i = 1; i < WIDTH; i = i + 1) begin : fa
        always @(*) begin
            {carry[i+1], sum[i]} = a[i] + b[i] + carry[i];
        end
    end
endgenerate

// Output carry and overflow
assign cout = carry[WIDTH];

// Overflow detection for signed addition:
// Overflow occurs when two positive numbers produce a negative result,
// or two negative numbers produce a positive result.
// This is detected by comparing the sign bits of inputs and output.
assign overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);

// Synchronous register update on rising edge of clock
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