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
reg [7:0] current_count;

// Sequential logic: clocked process
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        current_count <= 8'd0;
        overflow <= 1'b0;
    end else begin
        if (enable) begin
            current_count <= next_count;
            overflow <= (up_down && (next_count == 8'd255)) || (!up_down && (next_count == 8'd0));
        end else begin
            // Hold current value when disabled
            overflow <= 1'b0;
        end
    end
end

// Combinational logic: next state calculation
always @(*) begin
    next_count = current_count;
    if (enable) begin
        if (up_down) begin
            // Up counting
            if (current_count == 8'd255)
                next_count = 8'd0;
            else
                next_count = current_count + 1;
        end else begin
            // Down counting
            if (current_count == 8'd0)
                next_count = 8'd255;
            else
                next_count = current_count - 1;
        end
    end
end

// Assign output
assign count = current_count;

endmodule