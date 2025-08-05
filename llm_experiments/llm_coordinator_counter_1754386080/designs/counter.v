module counter (
    input clk,
    input reset,
    input enable,
    output reg [7:0] count
);

// 8-bit counter with asynchronous active-low reset and enable control
// Counts upward on each rising edge of clk when enable is high
// Wraps around to 0 after reaching maximum value (255)

always @(posedge clk or negedge reset) begin
    if (!reset) begin
        // Asynchronous reset: initialize count to 0 when reset is low
        count <= 8'b0;
    end else if (enable) begin
        // Increment count when enable is high
        count <= count + 1;
    end
    // No action when enable is low - retain current value
end

endmodule