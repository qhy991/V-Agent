module counter_4bit (
    input wire clk,
    input wire reset_n,
    input wire enable,
    output reg [3:0] count
);

always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
        count <= 4'b0000;
    end else if (enable) begin
        count <= count + 1;
    end
end

endmodule