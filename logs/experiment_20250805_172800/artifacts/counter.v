module counter (
    input      clk,
    input      reset,
    input      enable,
    output reg [7:0] count
);

always @(posedge clk or negedge reset) begin
    if (!reset) begin
        count <= 8'd0;
    end else if (enable) begin
        count <= count + 8'd1;
    end
end

endmodule