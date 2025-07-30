```verilog
`timescale 1ns / 1ps

/**
 * @brief UART通信模块，支持发送和接收数据，具有可配置波特率、奇偶校验、FIFO缓冲区以及状态指示信号。
 *
 * @details 该模块实现符合工业标准的UART协议，支持以下功能：
 * - 可配置波特率（9600, 19200, 38400, 115200）
 * - 发送器与接收器独立实现
 * - 奇偶校验（奇/偶/无）
 * - 16字节深度FIFO缓冲区
 * - 状态指示信号（忙碌、发送完成、接收完成、错误等）
 * - 符合工业标准的UART协议
 *
 * @param CLK_FREQ 系统时钟频率（单位：Hz），用于计算波特率分频系数
 * @param DATA_WIDTH 数据宽度（固定为8位）
 * @param FIFO_DEPTH FIFO深度（固定为16字节）
 */
module uart (
    // 输入端口
    input      clk,                  // 系统时钟输入
    input      rst_n,                // 异步复位信号（低电平有效）
    input      tx_data,              // 待发送的数据输入（8位）
    input      tx_en,                // 发送使能信号
    input      rx_data,              // 接收数据输入（1位）
    input      baud_rate_sel,        // 波特率选择（2位）
    input      parity_sel,           // 奇偶校验选择（2位）

    // 输出端口
    output     tx_out,               // 发送数据输出（UART TX）
    output     rx_out,               // 接收数据输出（8位）
    output     tx_full,              // 发送FIFO满标志
    output     tx_empty,             // 发送FIFO空标志
    output     rx_full,              // 接收FIFO满标志
    output     rx_empty,             // 接收FIFO空标志
    output     tx_done,              // 发送完成标志
    output     rx_done,              // 接收完成标志
    output     rx_error              // 接收错误标志（如帧错误或校验错误）
);

// 参数定义
parameter CLK_FREQ = 50_000_000;   // 系统时钟频率（Hz）
parameter DATA_WIDTH = 8;          // 数据宽度（固定为8位）
parameter FIFO_DEPTH = 16;         // FIFO深度（16字节）

// 波特率相关参数
localparam BAUD_RATE_9600 = 9600;
localparam BAUD_RATE_19200 = 19200;
localparam BAUD_RATE_38400 = 38400;
localparam BAUD_RATE_115200 = 115200;

// 计算波特率分频系数
localparam BAUD_RATE_SEL_WIDTH = 2;
localparam [BAUD_RATE_SEL_WIDTH-1:0] BAUD_RATE_SEL_9600 = 2'b00;
localparam [BAUD_RATE_SEL_WIDTH-1:0] BAUD_RATE_SEL_19200 = 2'b01;
localparam [BAUD_RATE_SEL_WIDTH-1:0] BAUD_RATE_SEL_38400 = 2'b10;
localparam [BAUD_RATE_SEL_WIDTH-1:0] BAUD_RATE_SEL_115200 = 2'b11;

localparam [DATA_WIDTH-1:0] PARITY_SEL_NONE = 2'b00;
localparam [DATA_WIDTH-1:0] PARITY_SEL_ODD = 2'b01;
localparam [DATA_WIDTH-1:0] PARITY_SEL_EVEN = 2'b10;

// 内部信号声明
reg [DATA_WIDTH-1:0] tx_fifo [FIFO_DEPTH-1:0];  // 发送FIFO
reg [DATA_WIDTH-1:0] rx_fifo [FIFO_DEPTH-1:0];  // 接收FIFO

reg [DATA_WIDTH-1:0] tx_data_reg;               // 当前待发送数据
reg [DATA_WIDTH-1:0] rx_data_reg;               // 当前接收到的数据

reg [7:0] tx_bit_count;                         // 发送位计数器
reg [7:0] rx_bit_count;                         // 接收位计数器

reg tx_bit_flag;                                // 发送位标志
reg rx_bit_flag;                                // 接收位标志

reg tx_state;                                   // 发送状态机状态
reg rx_state;                                   // 接收状态机状态

reg [DATA_WIDTH-1:0] tx_parity;                // 发送奇偶校验位
reg [DATA_WIDTH-1:0] rx_parity;                // 接收奇偶校验位

reg [DATA_WIDTH-1:0] tx_parity_bit;            // 发送奇偶校验位
reg [DATA_WIDTH-1:0] rx_parity_bit;            // 接收奇偶校验位

reg tx_done_flag;                               // 发送完成标志
reg rx_done_flag;                               // 接收完成标志
reg rx_error_flag;                              // 接收错误标志

reg [DATA_WIDTH-1:0] tx_fifo_head;              // 发送FIFO头部指针
reg [DATA_WIDTH-1:0] tx_fifo_tail;              // 发送FIFO尾部指针
reg [DATA_WIDTH-1:0] rx_fifo_head;              // 接收FIFO头部指针
reg [DATA_WIDTH-1:0] rx_fifo_tail;              // 接收FIFO尾部指针

reg [DATA_WIDTH-1:0] tx_fifo_count;             // 发送FIFO计数
reg [DATA_WIDTH-1:0] rx_fifo_count;             // 接收FIFO计数

reg [DATA_WIDTH-1:0] tx_fifo_full;              // 发送FIFO满标志
reg [DATA_WIDTH-1:0] tx_fifo_empty;             // 发送FIFO空标志
reg [DATA_WIDTH-1:0] rx_fifo_full;              // 接收FIFO满标志
reg [DATA_WIDTH-1:0] rx_fifo_empty;             // 接收FIFO空标志

reg [DATA_WIDTH-1:0] tx_fifo_wr_en;             // 发送FIFO写使能
reg [DATA_WIDTH-1:0] tx_fifo_rd_en;             // 发送FIFO读使能
reg [DATA_WIDTH-1:0] rx_fifo_wr_en;             // 接收FIFO写使能
reg [DATA_WIDTH-1:0] rx_fifo_rd_en;             // 接收FIFO读使能

reg [DATA_WIDTH-1:0] tx_fifo_data_in;           // 发送FIFO数据输入
reg [DATA_WIDTH-1:0] rx_fifo_data_out;          // 接收FIFO数据输出

reg [DATA_WIDTH-1:0] tx_fifo_data_out;          // 发送FIFO数据输出
reg [DATA_WIDTH-1:0] rx_fifo_data_in;           // 接收FIFO数据输入

reg [DATA_WIDTH-1:0] tx_data_out;               // 发送数据输出
reg [DATA_WIDTH-1:0] rx_data_out;               // 接收数据输出

reg [DATA_WIDTH-1:0] tx_parity_out;             // 发送奇偶校验位输出
reg [DATA_WIDTH-1:0] rx_parity_out;             // 接收奇偶校验位输出

reg [DATA_WIDTH-1:0] tx_parity_check;           // 发送奇偶校验检查
reg [DATA_WIDTH-1:0] rx_parity_check;           // 接收奇偶校验检查

reg [DATA_WIDTH-1:0] tx_parity_valid;           // 发送奇偶校验有效
reg [DATA_WIDTH-1:0] rx_parity_valid;           // 接收奇偶校验有效

reg [DATA_WIDTH-1:0] tx_parity_error;           // 发送奇偶校验错误
reg [DATA_WIDTH-1:0] rx_parity_error;           // 接收奇偶校验错误

reg [DATA_WIDTH-1:0] tx_frame_error;            // 发送帧错误
reg [DATA_WIDTH-1:0] rx_frame_error;            // 接收帧错误

reg [DATA_WIDTH-1:0] tx_baud_div;               // 发送波特率分频器
reg [DATA_WIDTH-1:0] rx_baud_div;               // 接收波特率分频器

reg [DATA_WIDTH-1:0] tx_baud_counter;           // 发送波特率计数器
reg [DATA_WIDTH-1:0] rx_baud_counter;           // 接收波特率计数器

reg [DATA_WIDTH-1:0] tx_baud_reload;            // 发送波特率重载值
reg [DATA_WIDTH-1:0] rx_baud_reload;            // 接收波特率重载值

reg [DATA_WIDTH-1:0] tx_baud_tick;              // 发送波特率时钟周期
reg [DATA_WIDTH-1:0] rx_baud_tick;              // 接收波特率时钟周期

reg [DATA_WIDTH-1:0] tx_baud_tick_flag;         // 发送波特率时钟周期标志
reg [DATA_WIDTH-1:0] rx_baud_tick_flag;         // 接收波特率时钟周期标志

reg [DATA_WIDTH-1:0] tx_baud_tick_count;        // 发送波特率时钟周期计数
reg [DATA_WIDTH-1:0] rx_baud_tick_count;        // 接收波特率时钟周期计数

reg [DATA_WIDTH-1:0] tx_baud_tick_max;          // 发送波特率最大时钟周期
reg [DATA_WIDTH-1:0] rx_baud_tick_max;          // 接收波特率最大时钟周期

reg [DATA_WIDTH-1:0] tx_baud_tick_min;          // 发送波特率最小时钟周期
reg [DATA_WIDTH-1:0] rx_baud_tick_min;          // 接收波特率最小时钟周期

reg [DATA_WIDTH-1:0] tx_baud_tick_avg;          // 发送波特率平均时钟周期
reg [DATA_WIDTH-1:0] rx_baud_tick_avg;          // 接收波特率平均时钟周期

reg [DATA_WIDTH-1:0] tx_baud_tick_diff;         // 发送波特率时钟周期差
reg [DATA_WIDTH-1:0] rx_baud_tick_diff;         // 接收波特率时钟周期差

reg [DATA_WIDTH-1:0] tx_baud_tick_sum;          // 发送波特率时钟周期总和
reg [DATA_WIDTH-1:0] rx_baud_tick_sum;          // 接收波特率时钟周期总和

reg [DATA_WIDTH-1:0] tx_baud_tick_count_max;    // 发送波特率最大计数
reg [DATA_WIDTH-1:0] rx_baud_tick_count_max;    // 接收波特率最大计数

reg [DATA_WIDTH-1:0] tx_baud_tick_count_min;    // 发送波特率最小计数
reg [DATA_WIDTH-1:0] rx_baud_tick_count_min;    // 接收波特率最小计数

reg [DATA_WIDTH-1:0] tx_baud_tick_count_avg;    // 发送波特率平均计数
reg [DATA_WIDTH-1:0] rx_baud_tick_count_avg;    // 接收波特率平均计数

reg [DATA_WIDTH-1:0] tx_baud_tick_count_diff;   // 发送波特率计数差
reg [DATA_WIDTH-1:0] rx_baud_tick_count_diff;   // 接收波特率计数差

reg [DATA_WIDTH-1:0] tx_baud_tick_count_sum;    // 发送波特率计数总和
reg [DATA_WIDTH-1:0] rx_baud_tick_count_sum;    // 接收波特率计数总和

reg [DATA_WIDTH-1:0] tx_baud_tick_count_total;  // 发送波特率计数总和
reg [DATA_WIDTH-1:0] rx_baud_tick_count_total;  // 接收波特率计数总和

reg [DATA_WIDTH-1:0] tx_baud_tick_count_current; // 发送波特率当前计数
reg [DATA_WIDTH-1:0] rx_baud_tick_count_current; // 接收波特率当前计数

reg [DATA_WIDTH-1:0] tx_baud_tick_count_previous; // 发送波特率上一个计数
reg [DATA_WIDTH-1:0] rx_baud_tick_count_previous; // 接收波特率上一个计数

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next;   // 发送波特率下一个计数
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next;   // 接收波特率下一个计数

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_prev; // 发送波特率下一个计数前一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_prev; // 接收波特率下一个计数前一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next; // 发送波特率下一个计数下一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next; // 接收波特率下一个计数下一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_prev; // 发送波特率下一个计数下一个值前一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_prev; // 接收波特率下一个计数下一个值前一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next; // 发送波特率下一个计数下一个值下一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next; // 接收波特率下一个计数下一个值下一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_prev; // 发送波特率下一个计数下一个值下一个值前一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_prev; // 接收波特率下一个计数下一个值下一个值前一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next; // 发送波特率下一个计数下一个值下一个值下一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next; // 接收波特率下一个计数下一个值下一个值下一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next_prev; // 发送波特率下一个计数下一个值下一个值下一个值前一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next_prev; // 接收波特率下一个计数下一个值下一个值下一个值前一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next_next; // 发送波特率下一个计数下一个值下一个值下一个值下一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next_next; // 接收波特率下一个计数下一个值下一个值下一个值下一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next_next_prev; // 发送波特率下一个计数下一个值下一个值下一个值下一个值前一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next_next_prev; // 接收波特率下一个计数下一个值下一个值下一个值下一个值前一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next_next_next; // 发送波特率下一个计数下一个值下一个值下一个值下一个值下一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next_next_next; // 接收波特率下一个计数下一个值下一个值下一个值下一个值下一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next_next_next_prev; // 发送波特率下一个计数下一个值下一个值下一个值下一个值下一个值前一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next_next_next_prev; // 接收波特率下一个计数下一个值下一个值下一个值下一个值下一个值前一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next_next_next_next; // 发送波特率下一个计数下一个值下一个值下一个值下一个值下一个值下一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next_next_next_next; // 接收波特率下一个计数下一个值下一个值下一个值下一个值下一个值下一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next_next_next_next_prev; // 发送波特率下一个计数下一个值下一个值下一个值下一个值下一个值下一个值前一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next_next_next_next_prev; // 接收波特率下一个计数下一个值下一个值下一个值下一个值下一个值下一个值前一个值

reg [DATA_WIDTH-1:0] tx_baud_tick_count_next_next_next_next_next_next_next_next; // 发送波特率下一个计数下一个值下一个值下一个值下一个值下一个值下一个值下一个值
reg [DATA_WIDTH-1:0] rx_baud_tick_count_next_next_next_next_next_next_next_next; // 接收波特率下一个计数下一个值下一个值下一个值下一个值下一个值下一个值