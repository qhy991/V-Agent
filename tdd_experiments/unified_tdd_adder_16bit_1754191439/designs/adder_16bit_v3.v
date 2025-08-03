module adder_16bit #(
    parameter WIDTH = 16
)(
    input  [WIDTH-1:0] a,
    input  [WIDTH-1:0] b,
    input           cin,
    output reg [WIDTH-1:0] sum,
    output reg      cout,
    output reg      overflow
);

// Internal carry signals
reg [WIDTH:0] c;

// Initialize carry chain
assign c[0] = cin;

// Generate full adders in a ripple-carry structure
always @(*) begin
    // Initialize sum and carry
    sum = 0;
    c[0] = cin;

    // Ripple-carry adder loop
    for (int i = 0; i < WIDTH; i = i + 1) begin
        {c[i+1], sum[i]} = a[i] + b[i] + c[i];
    end

    // Output carry from the most significant bit
    cout = c[WIDTH];

    // Overflow detection: when two operands with same sign produce result with opposite sign
    // For signed numbers: overflow occurs if (a[15] == b[15]) && (sum[15] != a[15])
    overflow = (a[WIDTH-1] == b[WIDTH-1]) && (a[WIDTH-1] != sum[WIDTH-1]);
end

endmodule