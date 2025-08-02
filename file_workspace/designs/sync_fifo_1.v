module sync_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 16
)(
    input clk,
    input rst_n,
    input wr_en,
    input rd_en,
    output reg full,
    output reg empty
);

localparam ADDR_WIDTH = $clog2(DEPTH);

reg [ADDR_WIDTH-1:0] wr_ptr;
reg [ADDR_WIDTH-1:0] rd_ptr;
reg [ADDR_WIDTH-1:0] next_wr_ptr;
reg [ADDR_WIDTH-1:0] next_rd_ptr;

reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        wr_ptr <= 0;
        rd_ptr <= 0;
        full <= 1'b1;
        empty <= 1'b1;
    end else begin
        if (wr_en && !full) begin
            mem[wr_ptr] <= data_in;
            wr_ptr <= next_wr_ptr;
        end
        if (rd_en && !empty) begin
            data_out <= mem[rd_ptr];
            rd_ptr <= next_rd_ptr;
        end
        full <= (wr_ptr == next_rd_ptr) ? 1'b1 : 1'b0;
        empty <= (rd_ptr == next_wr_ptr) ? 1'b1 : 1'b0;
    end
end

always @(*) begin
    next_wr_ptr = wr_ptr + 1;
    next_rd_ptr = rd_ptr + 1;
    if (next_wr_ptr == DEPTH) begin
        next_wr_ptr = 0;
    end
    if (next_rd_ptr == DEPTH) begin
        next_rd_ptr = 0;
    end
end

endmodule