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

// Overflow detection logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        overflow <= 1'b0;
    end else begin
        if (enable) begin
            if (up_down) begin
                if (count == 8'hFF) begin
                    overflow <= 1'b1;
                end else begin
                    overflow <= 1'b0;
                end
            end else begin
                if (count == 8'h00) begin
                    overflow <= 1'b1;
                end else begin
                    overflow <= 1'b0;
                end
            end
        end
    end
end

// Counting logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'h00;
    end else begin
        if (enable) begin
            if (up_down) begin
                next_count = count + 1;
            end else begin
                next_count = count - 1;
            end
            count <= next_count;
        end
    end
end

endmodule