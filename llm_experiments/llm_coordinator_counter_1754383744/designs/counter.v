module counter(
    input wire clk,
    input wire rst,
    input wire enable,
    output reg [3:0] count
);

always @(posedge clk or posedge rst) begin
    if (rst)
        count <= 4'b0;
    else if (enable)
        count <= count + 1;
end

endmodule