module example_module (
    input clk,
    input rst_n,
    output reg [7:0] data_out
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= 8'b0;
        end else begin
            data_out <= data_out + 1;
        end
    end

endmodule