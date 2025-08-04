module counter_8bit (
    input wire clk,
    input wire rst_n,
    input wire enable,
    output reg [7:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'b0;
        else if (enable)
            count <= count + 1;
    end

endmodule