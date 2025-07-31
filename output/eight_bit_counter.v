module eight_bit_counter (
    input clk,
    input rst_n,
    input en,
    output reg [7:0] count,
    output reg overflow
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'b0;
            overflow <= 1'b0;
        end else if (en) begin
            if (count == 8'b11111111) begin
                count <= 8'b0;
                overflow <= 1'b1;
            end else begin
                count <= count + 1;
                overflow <= 1'b0;
            end
        end
    end

endmodule