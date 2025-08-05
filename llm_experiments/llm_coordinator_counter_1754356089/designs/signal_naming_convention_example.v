module example_module (
    input  wire        i_clk,              // 时钟输入
    input  wire        i_rst_n,          // 异步复位，低电平有效
    input  wire [7:0]  i_data_in,        // 数据输入
    input  wire        i_enable,         // 使能信号
    output wire [7:0]  o_data_out,       // 数据输出
    output wire        o_valid           // 有效信号
);

    // 内部信号使用s_前缀
    wire [7:0] s_data_reg;          // 数据寄存器
    wire       s_enable_reg;        // 使能寄存器
    wire       s_valid_int;         // 内部有效信号
    
    // 时序逻辑：寄存器赋值
    always @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            s_data_reg <= 8'h00;
            s_enable_reg <= 1'b0;
        end else begin
            s_data_reg <= i_data_in;
            s_enable_reg <= i_enable;
        end
    end
    
    // 组合逻辑：输出生成
    assign s_valid_int = s_enable_reg & (s_data_reg != 8'h00);
    assign o_data_out = s_data_reg;
    assign o_valid = s_valid_int;
    
endmodule