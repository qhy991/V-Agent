module eight_bit_counter (
    input clk,
    input rst_n,
    input en,
    input load,
    input [7:0] d,
    output reg [7:0] q
);

    always @(posedge clk) begin
        if (!rst_n) begin
            q <= 8'b0;
        end else if (en) begin
            if (load) begin
                q <= d;
            end else begin
                q <= q + 1;
            end
        end
    end

endmodule