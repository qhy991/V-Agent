module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output wire [31:0] result,
    output wire zero,
    output wire overflow
);

// 内部信号声明
wire [31:0] add_result;
wire [31:0] sub_result;
wire [31:0] and_result;
wire [31:0] or_result;
wire [31:0] xor_result;
wire [31:0] not_result;
wire [31:0] eq_result;
wire [31:0] lt_result;
wire [31:0] gt_result;

// 组合逻辑：算术运算
assign add_result = a + b;
assign sub_result = a - b;

// 组合逻辑：逻辑运算
assign and_result = a & b;
assign or_result  = a | b;
assign xor_result = a ^ b;
assign not_result = ~a;

// 组合逻辑：比较运算（结果为32位全1或全0）
assign eq_result = (a == b) ? 32'b1 : 32'b0;
assign lt_result = (a < b) ? 32'b1 : 32'b0;
assign gt_result = (a > b) ? 32'b1 : 32'b0;

// 组合逻辑：选择最终结果
assign result = 
    (op == 4'b0000) ? add_result :
    (op == 4'b0001) ? sub_result :
    (op == 4'b0010) ? and_result :
    (op == 4'b0011) ? or_result :
    (op == 4'b0100) ? xor_result :
    (op == 4'b0101) ? not_result :
    (op == 4'b0110) ? eq_result :
    (op == 4'b0111) ? lt_result :
    (op == 4'b1000) ? gt_result :
                     32'd0;

// 零标志：结果为0时置1
assign zero = (result == 32'd0);

// 溢出标志：仅对ADD和SUB有效，使用符号位检测
// 对于有符号加法：若两正数相加得负，或两负数相加得正，则溢出
wire a_sign = a[31];
wire b_sign = b[31];
wire res_sign = result[31];

assign overflow = 
    (op == 4'b0000) ? // ADD
        (a_sign == b_sign) && (a_sign != res_sign) :
    (op == 4'b0001) ? // SUB
        (a_sign != b_sign) && (a_sign != res_sign) :
        1'b0;

endmodule