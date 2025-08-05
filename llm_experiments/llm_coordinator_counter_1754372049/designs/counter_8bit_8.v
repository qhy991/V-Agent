module counter_8bit (
    input clk,
    input rst,
    input enable,
    input up_down,
    output reg [7:0] count,
    output reg overflow
);

// 内部信号声明
reg [7:0] next_count;

// 计数逻辑
always @(posedge clk or negedge rst) begin
    if (!rst) begin
        count <= 8'b0;
        overflow <= 1'b0;
    end else begin
        if (enable) begin
            if (up_down) begin
                // 上计数模式
                if (count == 8'b11111111) begin
                    next_count <= 8'b0;
                    overflow <= 1'b1;
                end else begin
                    next_count <= count + 1;
                    overflow <= 1'b0;
                end
            end else begin
                // 下计数模式
                if (count == 8'b00000000) begin
                    next_count <= 8'b11111111;
                    overflow <= 1'b1;
                end else begin
                    next_count <= count - 1;
                    overflow <= 1'b0;
                end
            end
        end else begin
            next_count <= count;
            overflow <= 1'b0;
        end
        count <= next_count;
    end
end

endmodule