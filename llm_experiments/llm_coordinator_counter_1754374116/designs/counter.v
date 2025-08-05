module counter (
    input      clk,      // 主时钟输入，上升沿触发
    input      rst,      // 同步复位信号，高电平有效
    output reg [3:0] count // 4位计数器输出，范围0-15
);

    // 功能说明：
    // 该模块实现一个4位二进制向上计数器。
    // 在每个时钟上升沿，计数器值递增1。
    // 当计数器达到最大值15时，自动回滚到0（模16计数）。
    // 复位信号为高电平时，计数器同步清零。

    // 时序逻辑块：在时钟上升沿或复位信号有效时执行
    always @(posedge clk) begin
        if (rst) begin
            // 同步复位：当rst为高时，计数器清零
            count <= 4'b0;
        end else begin
            // 正常计数操作：递增计数器值
            count <= count + 1'b1;
        end
    end

endmodule