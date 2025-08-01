module error_module (
    input wire clk,
    input wire rst,
    output reg [7:0] data_out
);

always @(posedge clk) begin
    if (rst) begin
        data_out <= 8'b0;
    end
    else begin
        data_out <= data_out + 1; // 这里缺少分号
    end
end

endmodule