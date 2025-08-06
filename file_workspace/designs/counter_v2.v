module counter(
    input clk,
    input rst,
    input en,
    output reg [7:0] count
);
    // 时序逻辑：在时钟上升沿触发
    always @(posedge clk) begin
        // 异步复位：当rst为高电平时，count清零
        if (rst) begin
            count <= 8'b0;
        end
        // 使能信号控制计数器是否递增
        else if (en) begin
            count <= count + 1;
        end
        // 否则保持当前值
        else begin
            count <= count;
        end
    end
endmodule