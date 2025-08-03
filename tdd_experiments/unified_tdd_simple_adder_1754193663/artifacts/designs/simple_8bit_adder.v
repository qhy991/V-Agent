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

// Sequential logic: register outputs on clock edge
always @(posedge clk or posedge rst) begin
    if (rst) begin
        sum <= 8'b0;
        cout <= 1'b0;
        carry <= 8'b0;
    end else begin
        // Initialize carry chain
        carry[0] <= cin;
        
        // Ripple-carry adder logic
        // Each bit computes sum and propagate carry
        for (int i = 0; i < WIDTH; i++) begin
            {carry[i+1], sum[i]} = a[i] + b[i] + carry[i];
        end
        
        // Output final carry
        cout <= carry[WIDTH];
    end
end

endmodule