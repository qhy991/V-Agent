module counter (
    input      clk,
    input      reset,
    input      enable,
    output reg [7:0] count
);

    // 8-bit up counter with synchronous reset and enable
    // Counts on rising edge of clk
    // Synchronous active-high reset sets count to 0
    // Count increments only when enable is high
    // Rolls over to 0 when reaching 255

    always @(posedge clk) begin
        if (reset) begin
            count <= 8'd0;        // Reset value when reset is high
        end else if (enable) begin
            count <= count + 1;   // Increment count when enabled
        end
        // No action when enable is low (hold previous value)
    end

endmodule