module counter #(
    parameter WIDTH = 8
) (
    input        clk,
    input        rst,
    input        en,
    input        load,
    input  [WIDTH-1:0] data_in,
    output [WIDTH-1:0] count,
    output       carry_out
);

    // 内部寄存器声明
    reg [WIDTH-1:0] count_reg;
    reg carry_out_reg;

    // 主时序逻辑：同步复位、加载、递增控制
    always @(posedge clk) begin
        if (rst) begin
            count_reg   <= 0;
            carry_out_reg <= 0;
        end
        else if (load) begin
            count_reg   <= data_in;
            carry_out_reg <= 0;  // 加载时清除进位
        end
        else if (en) begin
            // 递增操作
            if (count_reg == {WIDTH{1'b1}}) begin
                count_reg   <= 0;
                carry_out_reg <= 1'b1;  // 最大值递增时产生进位脉冲
            end else begin
                count_reg   <= count_reg + 1;
                carry_out_reg <= 0;  // 非最大值递增时不产生进位
            end
        end else begin
            // 保持状态
            carry_out_reg <= 0;
        end
    end

    // 输出连接
    assign count      = count_reg;
    assign carry_out  = carry_out_reg;

endmodule