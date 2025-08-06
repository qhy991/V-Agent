module counter_8bit (
    input clk,
    input rst_n,
    input en,
    output reg [7:0] count
);

// 时序逻辑：在时钟上升沿触发，异步复位
always @(posedge clk) begin
    if (!rst_n) begin
        // 异步复位，将计数值清零
        count <= 8'd0;
    end else if (en) begin
        // 当使能信号有效时，计数器递增
        count <= count + 1'b1;
    end
    // 否则保持当前值（不计数）
end

endmodule