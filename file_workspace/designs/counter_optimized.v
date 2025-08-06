module counter (
    input clk,
    input rst_n,
    input en,
    output reg [3:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 4'b0;
    end else if (en) begin
        count <= count + 1;
    end
end

// Add synthesis directives for area optimization
`ifdef SYNTHESIS
    (* keep = "true" *)
    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 4'b0;
        end else if (en) begin
            count <= count + 1;
        end
    end
`endif

endmodule