module simple_counter(
    input clk,
    input rst_n,
    input enable,
    output reg [7:0] count,
    output overflow
);

assign overflow = (count == 8'hFF);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        count <= 8'b0;
    else if (enable)
        count <= count + 1;
end

endmodule