module counter (
    input      clk,
    input      rst_n,
    input      en,
    output reg [7:0] count
);

    // 使用异步复位、同步释放（推荐实践）
    // 但为最小化面积，保持原复位行为
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'd0;
        end else begin
            count <= count + en;  // 关键优化：用加 en 替代条件赋值
        end
    end

endmodule