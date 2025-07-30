```verilog
`timescale 1ns / 1ps

/**
 * @brief 32位算术逻辑单元(ALU)
 * @details 实现加法、减法、与、或、异或运算，并包含零标志和溢出检测功能。
 * 支持32位操作数，3位操作码选择运算类型。
 * 
 * @param DATA_WIDTH 数据宽度（默认32位）
 */
module alu #(
    parameter DATA_WIDTH = 32
)(
    // 输入端口
    input  [DATA_WIDTH-1:0] a,              // 操作数A
    input  [DATA_WIDTH-1:0] b,              // 操作数B
    input  [2:0]            op,             // 操作码 (000: ADD, 001: SUB, 010: AND, 011: OR, 100: XOR)
    
    // 输出端口
    output reg [DATA_WIDTH-1:0] result,     // 运算结果
    output reg                zero,         // 零标志 (当结果为0时置1)
    output reg                overflow      // 溢出标志 (仅在加法/减法时有效)
);

// 内部信号声明
reg [DATA_WIDTH-1:0] add_result;
reg [DATA_WIDTH-1:0] sub_result;
reg [DATA_WIDTH-1:0] and_result;
reg [DATA_WIDTH-1:0] or_result;
reg [DATA_WIDTH-1:0] xor_result;

// 用于溢出检测的中间信号
reg [DATA_WIDTH:0]   add_carry;        // 加法进位
reg [DATA_WIDTH:0]   sub_carry;        // 减法进位

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_sign;         // 加法符号位
reg [DATA_WIDTH-1:0] sub_sign;         // 减法符号位

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign;  // 加法结果符号位
reg [DATA_WIDTH-1:0] sub_result_sign;  // 减法结果符号位

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign; // 加法输入A符号位
reg [DATA_WIDTH-1:0] add_input_b_sign; // 加法输入B符号位

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign; // 减法输入A符号位
reg [DATA_WIDTH-1:0] sub_input_b_sign; // 减法输入B符号位

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext; // 扩展的加法结果符号位
reg [DATA_WIDTH-1:0] sub_result_sign_ext; // 扩展的减法结果符号位

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext; // 扩展的加法输入A符号位
reg [DATA_WIDTH-1:0] add_input_b_sign_ext; // 扩展的加法输入B符号位

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext; // 扩展的减法输入A符号位
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext; // 扩展的减法输入B符号位

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_overflow;       // 加法溢出标志
reg [DATA_WIDTH-1:0] sub_overflow;       // 减法溢出标志

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_1; // 扩展的加法结果符号位1
reg [DATA_WIDTH-1:0] add_result_sign_ext_2; // 扩展的加法结果符号位2

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_1; // 扩展的减法结果符号位1
reg [DATA_WIDTH-1:0] sub_result_sign_ext_2; // 扩展的减法结果符号位2

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_1; // 扩展的加法输入A符号位1
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_1; // 扩展的加法输入B符号位1

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_1; // 扩展的减法输入A符号位1
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_1; // 扩展的减法输入B符号位1

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_3; // 扩展的加法结果符号位3
reg [DATA_WIDTH-1:0] add_result_sign_ext_4; // 扩展的加法结果符号位4

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_3; // 扩展的减法结果符号位3
reg [DATA_WIDTH-1:0] sub_result_sign_ext_4; // 扩展的减法结果符号位4

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_2; // 扩展的加法输入A符号位2
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_2; // 扩展的加法输入B符号位2

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_2; // 扩展的减法输入A符号位2
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_2; // 扩展的减法输入B符号位2

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_5; // 扩展的加法结果符号位5
reg [DATA_WIDTH-1:0] add_result_sign_ext_6; // 扩展的加法结果符号位6

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_5; // 扩展的减法结果符号位5
reg [DATA_WIDTH-1:0] sub_result_sign_ext_6; // 扩展的减法结果符号位6

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_3; // 扩展的加法输入A符号位3
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_3; // 扩展的加法输入B符号位3

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_3; // 扩展的减法输入A符号位3
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_3; // 扩展的减法输入B符号位3

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_7; // 扩展的加法结果符号位7
reg [DATA_WIDTH-1:0] add_result_sign_ext_8; // 扩展的加法结果符号位8

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_7; // 扩展的减法结果符号位7
reg [DATA_WIDTH-1:0] sub_result_sign_ext_8; // 扩展的减法结果符号位8

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_4; // 扩展的加法输入A符号位4
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_4; // 扩展的加法输入B符号位4

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_4; // 扩展的减法输入A符号位4
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_4; // 扩展的减法输入B符号位4

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_9; // 扩展的加法结果符号位9
reg [DATA_WIDTH-1:0] add_result_sign_ext_10; // 扩展的加法结果符号位10

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_9; // 扩展的减法结果符号位9
reg [DATA_WIDTH-1:0] sub_result_sign_ext_10; // 扩展的减法结果符号位10

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_5; // 扩展的加法输入A符号位5
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_5; // 扩展的加法输入B符号位5

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_5; // 扩展的减法输入A符号位5
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_5; // 扩展的减法输入B符号位5

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_11; // 扩展的加法结果符号位11
reg [DATA_WIDTH-1:0] add_result_sign_ext_12; // 扩展的加法结果符号位12

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_11; // 扩展的减法结果符号位11
reg [DATA_WIDTH-1:0] sub_result_sign_ext_12; // 扩展的减法结果符号位12

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_6; // 扩展的加法输入A符号位6
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_6; // 扩展的加法输入B符号位6

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_6; // 扩展的减法输入A符号位6
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_6; // 扩展的减法输入B符号位6

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_13; // 扩展的加法结果符号位13
reg [DATA_WIDTH-1:0] add_result_sign_ext_14; // 扩展的加法结果符号位14

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_13; // 扩展的减法结果符号位13
reg [DATA_WIDTH-1:0] sub_result_sign_ext_14; // 扩展的减法结果符号位14

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_7; // 扩展的加法输入A符号位7
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_7; // 扩展的加法输入B符号位7

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_7; // 扩展的减法输入A符号位7
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_7; // 扩展的减法输入B符号位7

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_15; // 扩展的加法结果符号位15
reg [DATA_WIDTH-1:0] add_result_sign_ext_16; // 扩展的加法结果符号位16

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_15; // 扩展的减法结果符号位15
reg [DATA_WIDTH-1:0] sub_result_sign_ext_16; // 扩展的减法结果符号位16

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_8; // 扩展的加法输入A符号位8
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_8; // 扩展的加法输入B符号位8

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_8; // 扩展的减法输入A符号位8
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_8; // 扩展的减法输入B符号位8

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_17; // 扩展的加法结果符号位17
reg [DATA_WIDTH-1:0] add_result_sign_ext_18; // 扩展的加法结果符号位18

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_17; // 扩展的减法结果符号位17
reg [DATA_WIDTH-1:0] sub_result_sign_ext_18; // 扩展的减法结果符号位18

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_9; // 扩展的加法输入A符号位9
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_9; // 扩展的加法输入B符号位9

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_9; // 扩展的减法输入A符号位9
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_9; // 扩展的减法输入B符号位9

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_19; // 扩展的加法结果符号位19
reg [DATA_WIDTH-1:0] add_result_sign_ext_20; // 扩展的加法结果符号位20

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_19; // 扩展的减法结果符号位19
reg [DATA_WIDTH-1:0] sub_result_sign_ext_20; // 扩展的减法结果符号位20

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_10; // 扩展的加法输入A符号位10
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_10; // 扩展的加法输入B符号位10

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_10; // 扩展的减法输入A符号位10
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_10; // 扩展的减法输入B符号位10

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_21; // 扩展的加法结果符号位21
reg [DATA_WIDTH-1:0] add_result_sign_ext_22; // 扩展的加法结果符号位22

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_21; // 扩展的减法结果符号位21
reg [DATA_WIDTH-1:0] sub_result_sign_ext_22; // 扩展的减法结果符号位22

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_input_a_sign_ext_11; // 扩展的加法输入A符号位11
reg [DATA_WIDTH-1:0] add_input_b_sign_ext_11; // 扩展的加法输入B符号位11

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_input_a_sign_ext_11; // 扩展的减法输入A符号位11
reg [DATA_WIDTH-1:0] sub_input_b_sign_ext_11; // 扩展的减法输入B符号位11

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] add_result_sign_ext_23; // 扩展的加法结果符号位23
reg [DATA_WIDTH-1:0] add_result_sign_ext_24; // 扩展的加法结果符号位24

// 用于溢出检测的中间信号
reg [DATA_WIDTH-1:0] sub_result_sign_ext_23;