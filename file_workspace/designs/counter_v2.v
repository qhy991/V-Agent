module counter (
    input clk,
    input rst_n,
    input en,
    output reg [7:0] count
);

// 时序逻辑：在时钟上升沿触发
always @(posedge clk) begin
    // 同步复位：当rst_n为低电平时，计数器清零
    if (!rst_n) begin
        count <= 8'd0;
    end
    // 当使能信号有效且未复位时，计数器递增
    else if (en) begin
        count <= count + 1'b1;
    end
    // 否则保持当前值（不递增）
end

endmodule