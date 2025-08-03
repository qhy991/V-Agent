module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output wire [31:0] result,
    output wire zero
);

// 内部信号声明
wire [31:0] add_result;
wire [31:0] sub_result;
wire [31:0] and_result;
wire [31:0] or_result;
wire [31:0] xor_result;
wire [31:0] sll_result;
wire [31:0] srl_result;

// 组合逻辑实现：7种运算
assign add_result = a + b;
assign sub_result = a - b;
assign and_result = a & b;
assign or_result  = a | b;
assign xor_result = a ^ b;
assign sll_result = {b[31:5], {5{1'b0}}} << b[4:0];  // SLL: 左移，低位补0
assign srl_result = {32 - b[4:0]{1'b0}, b[31:b[4:0]]};  // SRL: 右移，高位补0

// 多路选择器：根据操作码选择结果
assign result = 
    (op == 4'd0) ? add_result :  // ADD
    (op == 4'd1) ? sub_result :  // SUB
    (op == 4'd2) ? and_result :  // AND
    (op == 4'd3) ? or_result :   // OR
    (op == 4'd4) ? xor_result :  // XOR
    (op == 4'd5) ? sll_result :  // SLL
    (op == 4'd6) ? srl_result :  // SRL
    32'd0;                      // 默认（未定义操作码）

// 零标志：result为0时输出1，否则0
assign zero = (result == 32'd0) ? 1'b1 : 1'b0;

endmodule