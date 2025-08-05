// Verilog/SystemVerilog 信号命名规范示例

// 1. 基本命名规则
module signal_naming_example (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] data_in,
    output wire [7:0] data_out,
    output wire valid_out
);

    // 2. 信号命名示例
    wire [7:0] internal_data;     // 内部数据总线
    wire       flag_valid;         // 标志信号
    wire [3:0] counter_value;      // 计数器值
    wire       state_idle;         // 状态标志
    wire       enable_signal;      // 使能信号
    
    // 3. 复合信号命名
    wire [7:0] addr_bus;           // 地址总线
    wire [31:0] data_bus;          // 数据总线
    wire [2:0] sel_bus;            // 选择总线
    
    // 4. 时序信号命名
    wire       sync_clk;           // 同步时钟
    wire       async_rst;          // 异步复位
    wire       sync_rst;           // 同步复位
    
    // 5. 接口信号命名
    wire [7:0] tx_data;            // 发送数据
    wire [7:0] rx_data;            // 接收数据
    wire       tx_valid;           // 发送有效
    wire       rx_valid;           // 接收有效
    wire       tx_ready;           // 发送就绪
    wire       rx_ready;           // 接收就绪
    
    // 6. 状态机信号命名
    typedef enum logic [1:0] {
        IDLE = 2'b00,
        READ = 2'b01,
        WRITE = 2'b10,
        DONE = 2'b11
    } state_t;
    
    state_t current_state, next_state;
    
endmodule

// 命名约定总结:
// 1. 使用有意义的描述性名称
// 2. 保持一致性
// 3. 避免缩写和模糊名称
// 4. 区分输入/输出/内部信号
// 5. 使用下划线分隔单词
// 6. 遵循团队/项目命名规范