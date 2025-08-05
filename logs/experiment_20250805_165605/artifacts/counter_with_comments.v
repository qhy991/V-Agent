module counter_with_comments (
    input      clk,        // 时钟信号，上升沿触发
    input      reset,      // 同步复位信号，高电平有效
    input      enable,     // 计数使能信号，高电平允许计数
    output reg [7:0] count // 当前8位计数值输出
);

// 计数器逻辑实现
// 在时钟上升沿触发
always @(posedge clk) begin
    if (reset) begin
        // 复位时计数值清零
        count <= 8'h0;
    end else if (enable) begin
        // 使能信号有效时递增计数值
        count <= count + 1;
    end
end

endmodule