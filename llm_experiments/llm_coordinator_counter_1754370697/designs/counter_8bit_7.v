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

// Count logic
always @(posedge clk or posedge rst) begin
    if (rst) begin
        count <= 8'b0;
        overflow <= 1'b0;
    end else begin
        if (enable) begin
            if (up_down) begin
                // Up count mode
                if (count == 8'b11111111) begin
                    next_count <= 8'b0;
                    overflow <= 1'b1;
                end else begin
                    next_count <= count + 1;
                    overflow <= 1'b0;
                end
            end else begin
                // Down count mode
                if (count == 8'b00000000) begin
                    next_count <= 8'b11111111;
                    overflow <= 1'b1;
                end else begin
                    next_count <= count - 1;
                    overflow <= 1'b0;
                end
            end
        end
    end
end

// Assign the next count value
always @(posedge clk or posedge rst) begin
    if (rst) begin
        count <= 8'b0;
    end else begin
        if (enable) begin
            count <= next_count;
        end
    end
end

endmodule