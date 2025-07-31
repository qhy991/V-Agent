module counter_4bit (
    input clk,
    input rst_n,
    input en,
    output reg [3:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 4'b0000;
    end else if (en) begin
        if (count == 4'b1111) begin
            count <= 4'b0000;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule