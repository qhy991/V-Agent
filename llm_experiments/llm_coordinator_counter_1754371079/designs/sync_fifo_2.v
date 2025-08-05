module sync_fifo #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 5
)(
    input clk,
    input rst_n,
    input wr_en,
    input rd_en,
    input [DATA_WIDTH-1:0] wr_data,
    output reg [DATA_WIDTH-1:0] rd_data,
    output reg full,
    output reg empty,
    output reg [ADDR_WIDTH-1:0] count
);

localparam DEPTH = 1 << ADDR_WIDTH;

reg [ADDR_WIDTH-1:0] wr_ptr;
reg [ADDR_WIDTH-1:0] rd_ptr;
reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        wr_ptr <= 0;
        rd_ptr <= 0;
        full <= 1'b0;
        empty <= 1'b1;
        count <= 0;
    end else begin
        if (wr_en && !full) begin
            mem[wr_ptr] <= wr_data;
            wr_ptr <= wr_ptr + 1;
            count <= count + 1;
        end

        if (rd_en && !empty) begin
            rd_data <= mem[rd_ptr];
            rd_ptr <= rd_ptr + 1;
            count <= count - 1;
        end

        full <= (count == DEPTH - 1);
        empty <= (count == 0);
    end
end

endmodule