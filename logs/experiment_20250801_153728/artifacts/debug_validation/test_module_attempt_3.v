module counter_8bit (
    input clk,
    input rst_n,
    input en,
    output reg [7:0] count,
    output reg overflow
);

// 同步复位，使能控制，计数器递增逻辑
always @(posedge clk) begin
    if (!rst_n) begin
        // 同步复位：清零计数器和溢出标志
        count <= 8'b0;
        overflow <= 1'b0;
    end else if (en) begin
        // 使能有效时进行计数
        if (count == 8'hFF) begin
            // 达到最大值（255）时触发溢出标志
            count <= 8'h00;
            overflow <= 1'b1;
        end else begin
            count <= count + 1;
            overflow <= 1'b0;
        end
    end else begin
        // 使能无效时保持当前状态
        overflow <= 1'b0;
    end
end

endmodule