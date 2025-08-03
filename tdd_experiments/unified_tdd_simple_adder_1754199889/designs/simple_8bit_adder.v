module simple_8bit_adder #(
    parameter WIDTH = 8
) (
    input               clk,
    input               rst,
    input  [WIDTH-1:0]  a,
    input  [WIDTH-1:0]  b,
    input               cin,
    output logic [WIDTH-1:0] sum,
    output logic        cout
);

// Internal signals for carry propagation
logic [WIDTH-1:0] c;

// Carry chain: generate carry bits using full adders
always_comb begin
    // Initialize first carry bit
    c[0] = cin;
    
    // Generate each sum and carry bit
    for (int i = 0; i < WIDTH; i++) begin
        // Full adder logic: sum = a[i] ^ b[i] ^ c[i], carry = (a[i] & b[i]) | (c[i] & (a[i] ^ b[i]))
        sum[i] = a[i] ^ b[i] ^ c[i];
        c[i+1] = (a[i] & b[i]) | (c[i] & (a[i] ^ b[i]));
    end
    
    // Output carry is the final carry from the most significant bit
    cout = c[WIDTH];
end

// Synchronous register update on clock edge
always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= '0;
        cout <= 1'b0;
    end else begin
        sum <= sum;
        cout <= cout;
    end
end

endmodule