module counter (
    input      clk,      // 主时钟信号，上升沿触发
    input      reset,    // 同步复位信号，高电平有效
    input      enable,   // 计数使能信号，高电平允许递增
    output reg [7:0] count // 8位计数输出，表示当前计数值
);

    // 时序逻辑：在时钟上升沿触发
    always @(posedge clk) begin
        // 同步复位：当reset为高电平时，将计数器清零
        if (reset) begin
            count <= 8'd0;  // 复位时计数值置为0
        end
        // 使能控制：仅当enable为高时进行递增
        else if (enable) begin
            count <= count + 1'b1;  // 计数值加1，自动处理8位溢出回绕（255+1=0）
        end
        // 当reset=0且enable=0时，保持当前计数值不变
        else begin
            count <= count;
        end
    end

endmodule