module counter (
    input clk,
    input rst_n,
    input en,
    output reg [7:0] count
);

// 时序逻辑：在时钟上升沿触发
always @(posedge clk) begin
    // 异步复位，低有效，优先级最高
    if (!rst_n) begin
        count <= 8'd0;
    end else if (en) begin
        // 当使能有效时，计数器递增
        // 达到最大值255后自动回绕到0
        if (count == 8'd255) begin
            count <= 8'd0;
        end else begin
            count <= count + 1'b1;
        end
    end
    // 否则保持当前值（en无效时）
end

endmodule