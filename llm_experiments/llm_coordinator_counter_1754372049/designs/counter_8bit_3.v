module counter_8bit (
    input clk,
    input rst,
    input enable,
    input up_down,
    output reg [7:0] count,
    output reg overflow
);

// Internal signals
reg [7:0] next_count;

// Overflow detection logic
always @(posedge clk or posedge rst) begin
    if (rst) begin
        overflow <= 1'b0;
    end else begin
        if (enable) begin
            if (up_down) begin
                // Up count
                if (count == 8'hFF) begin
                    overflow <= 1'b1;
                end else begin
                    overflow <= 1'b0;
                end
            end else begin
                // Down count
                if (count == 8'h00) begin
                    overflow <= 1'b1;
                end else begin
                    overflow <= 1'b0;
                end
            end
        end
    end
end

// Count update logic
always @(posedge clk or posedge rst) begin
    if (rst) begin
        count <= 8'h00;
    end else begin
        if (enable) begin
            if (up_down) begin
                // Up count
                next_count = count + 1;
            end else begin
                // Down count
                next_count = count - 1;
            end
            count <= next_count;
        end
    end
end

endmodule