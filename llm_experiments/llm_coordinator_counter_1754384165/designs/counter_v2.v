module counter (
    input      clk,
    input      reset,
    input      enable,
    output reg [7:0] count
);

// 8-bit counter with synchronous reset and enable control
// The counter increments only when 'enable' is high
// Reset takes effect only at rising edge of clock

always @(posedge clk) begin
    if (reset) begin
        count <= 8'h00;  // Synchronous reset sets counter to zero
    end else if (enable) begin
        count <= count + 1;  // Increment counter when enable is asserted
    end
    // No action when enable is low, retain current value
end

endmodule