module counter_8bit (
    input        clk,       // 时钟
    input        rst_n,     // 异步复位
    input        enable,    // 计数使能
    input        up_down,   // 计数方向(1:上计数, 0:下计数)
    output [7:0] count,     // 计数值
    output       overflow   // 溢出标志
);

    reg [7:0] count_reg;
    wire [7:0] next_count;

    // 计数逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count_reg <= 8'b0;
        end else if (enable) begin
            if (up_down) begin
                count_reg <= count_reg + 1;
            end else begin
                count_reg <= count_reg - 1;
            end
        end
    end

    // 溢出检测
    assign overflow = (count_reg == 8'hFF && up_down) || (count_reg == 8'h00 && !up_down);

    // 输出赋值
    assign count = count_reg;

endmodule