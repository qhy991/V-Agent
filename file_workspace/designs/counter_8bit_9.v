module counter_8bit (
    input clk,
    input rst_n,
    input enable,
    input up_down,
    output reg [7:0] count,
    output reg overflow
);

// Internal signals
reg [7:0] next_count;

// Asynchronous reset and synchronous update
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'b0;
        overflow <= 1'b0;
    end else begin
        if (enable) begin
            if (up_down) begin
                // Increment mode
                next_count = count + 1;
                if (next_count == 8'b0) begin
                    overflow <= 1'b1;
                end else begin
                    overflow <= 1'b0;
                end
            end else begin
                // Decrement mode
                next_count = count - 1;
                if (next_count == 8'b11111111) begin
                    overflow <= 1'b1;
                end else begin
                    overflow <= 1'b0;
                end
            end
            count <= next_count;
        end
    end
end

endmodule