module counter (
    input      clk,
    input      rst,
    input      enable,
    input      direction,
    output reg [3:0] count,
    output reg       overflow,
    output reg       underflow
);

    // Internal signal declarations
    reg [3:0] next_count;

    // Synchronous reset 4-bit up/down counter with overflow and underflow flags
    always @(posedge clk) begin
        if (rst) begin
            // Reset state: clear count and status flags
            count     <= 4'd0;
            overflow  <= 1'b0;
            underflow <= 1'b0;
        end else begin
            // Update count and flags based on enable and direction
            count <= next_count;

            // Assert overflow for one clock cycle when counting up from 15
            overflow  <= (enable && direction && (count == 4'd15)) ? 1'b1 : 1'b0;

            // Assert underflow for one clock cycle when counting down from 0
            underflow <= (enable && ~direction && (count == 4'd0)) ? 1'b1 : 1'b0;
        end
    end

    // Combinational logic to compute next count value
    always @(*) begin
        if (enable) begin
            if (direction)
                next_count = (count == 4'd15) ? 4'd0 : count + 1'b1;
            else
                next_count = (count == 4'd0)  ? 4'd15 : count - 1'b1;
        end else begin
            next_count = count;
        end
    end

endmodule