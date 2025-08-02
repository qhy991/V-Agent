module sync_fifo #(
    parameter DATA_WIDTH = 8,     // 数据位宽
    parameter FIFO_DEPTH = 16,    // FIFO深度
    parameter ADDR_WIDTH = 4      // 地址位宽 (log2(FIFO_DEPTH))
)(
    input                    clk,        // 时钟
    input                    rst_n,      // 异步复位（低电平有效）
    input                    wr_en,      // 写使能
    input                    rd_en,      // 读使能
    input  [DATA_WIDTH-1:0]  wr_data,    // 写数据
    output reg [DATA_WIDTH-1:0]  rd_data,    // 读数据
    output reg               full,       // 满标志
    output reg               empty,      // 空标志
    output reg [ADDR_WIDTH:0]    count       // FIFO中数据个数（ADDR_WIDTH+1位）
);

    // 内部信号
    reg [ADDR_WIDTH-1:0] wr_ptr;   // 写指针
    reg [ADDR_WIDTH-1:0] rd_ptr;   // 读指针
    
    // FIFO存储器 - 使用寄存器阵列
    reg [DATA_WIDTH-1:0] fifo_mem [0:FIFO_DEPTH-1];
    
    // 写操作和读操作控制
    wire wr_en_safe = wr_en & !full;   // 安全写使能
    wire rd_en_safe = rd_en & !empty;  // 安全读使能
    
    // 主要逻辑 - 异步复位，同步操作
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // 异步复位
            wr_ptr <= 0;
            rd_ptr <= 0;
            count <= 0;
            full <= 1'b0;
            empty <= 1'b1;
            rd_data <= 0;
        end else begin
            // 写操作
            if (wr_en_safe) begin
                fifo_mem[wr_ptr] <= wr_data;
                wr_ptr <= (wr_ptr == FIFO_DEPTH-1) ? 0 : wr_ptr + 1;
            end
            
            // 读操作
            if (rd_en_safe) begin
                rd_data <= fifo_mem[rd_ptr];
                rd_ptr <= (rd_ptr == FIFO_DEPTH-1) ? 0 : rd_ptr + 1;
            end
            
            // 计数器更新
            case ({wr_en_safe, rd_en_safe})
                2'b01: count <= count - 1;  // 只读
                2'b10: count <= count + 1;  // 只写
                2'b11: count <= count;      // 同时读写，count不变
                default: count <= count;    // 都不操作
            endcase
            
            // 状态标志更新
            case ({wr_en_safe, rd_en_safe})
                2'b01: begin  // 只读
                    full <= 1'b0;
                    empty <= (count == 1);  // 读完这个就空了
                end
                2'b10: begin  // 只写
                    empty <= 1'b0;
                    full <= (count == FIFO_DEPTH-1);  // 写完这个就满了
                end
                2'b11: begin  // 同时读写
                    // 状态不变
                end
                default: begin  // 都不操作
                    full <= (count == FIFO_DEPTH);
                    empty <= (count == 0);
                end
            endcase
        end
    end

endmodule