module counter (
    input      clk,
    input      reset,
    input      enable,
    output reg [7:0] count
);

// 8-bit counter with clock, asynchronous active-low reset, and enable control

always @(posedge clk) begin : counter_proc
    // Handle asynchronous reset (active low)
    if (!reset) begin
        count <= 8'h00;  // Reset the counter to zero
    end else if (enable) begin
        count <= count + 1;  // Increment counter when enable is asserted
    end
    // No action when enable is low
end

endmodule