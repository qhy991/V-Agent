module simple_adder #(
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

// Internal signals for ripple carry
reg [WIDTH-1:0] internal_sum;
reg [WIDTH-1:0] carry;

// Initialize carry chain
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 8'd0;
        cout <= 1'b0;
        carry <= 8'd0;
    end else begin
        // Ripple carry adder implementation
        // Start with input carry
        carry[0] <= cin;
        
        // Generate each bit of sum and carry
        for (int i = 0; i < WIDTH; i = i + 1) begin
            {carry[i+1], internal_sum[i]} = a[i] + b[i] + carry[i];
        end
        
        // Assign final outputs
        sum <= internal_sum;
        cout <= carry[WIDTH];
    end
end

endmodule