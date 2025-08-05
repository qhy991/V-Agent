module counter (
    input      clk,
    input      reset,
    input      enable,
    output reg [7:0] count
);

// 8-bit counter with synchronous active-high reset and enable control
// Counts upward on each positive clock edge only when enable is high
// Automatically wraps around upon reaching maximum value (255 -> 0)

always @(posedge clk) begin : counter_proc
    // Apply synchronous reset first
    if (reset) begin
        count <= 8'h00;
    end
    // Only increment when enable is high
    else if (enable) begin
        count <= count + 1;
    end
    // No action when enable is low - retain current value
end

endmodule