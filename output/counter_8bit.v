module counter_8bit (
    input clk,
    input rst,
    input en,
    output reg [7:0] count
);

    always @(posedge clk) begin
        if (rst) begin
            count <= 8'b0;
        end else if (en) begin
            if (count == 8'b11111111) begin
                count <= 8'b0;
            end else begin
                count <= count + 1;
            end
        end
    end

endmodule