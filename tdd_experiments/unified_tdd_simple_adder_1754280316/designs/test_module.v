module test_module(
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] data_in,
    output wire [7:0] data_out
);

    reg [7:0] delay_reg;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            delay_reg <= 8'h00;
        end else begin
            delay_reg <= data_in;
        end
    end
    
    assign data_out = delay_reg;
    
endmodule