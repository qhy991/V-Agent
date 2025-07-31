module counter_8bit(
    input clk,
    input reset,
    input enable,
    input [7:0] load_data,
    input load,
    output reg [7:0] count
);
    always @(posedge clk or posedge reset) begin
        if (reset)
            count <= 8'b0;
        else if (load)
            count <= load_data;
        else if (enable)
            count <= count + 1;
    end
endmodule