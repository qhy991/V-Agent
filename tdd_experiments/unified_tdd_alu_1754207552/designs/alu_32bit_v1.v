module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output wire   [31:0] result,
    output wire       zero,
    output wire       overflow
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

// 算术运算：加法与减法
assign add_result = a + b;
assign sub_result = a - b;

// 逻辑运算
assign and_result = a & b;
assign or_result  = a | b;
assign xor_result = a ^ b;
assign not_result = ~a;

// 比较运算（结果为32位全1或全0）
assign eq_result = (a == b) ? {32{1'b1}} : {32{1'b0}};
assign lt_result = (a < b) ? {32{1'b1}} : {32{1'b0}};
assign gt_result = (a > b) ? {32{1'b1}} : {32{1'b0}};

// 选择最终结果
assign result = 
    (op == 4'b0000) ? add_result :
    (op == 4'b0001) ? sub_result :
    (op == 4'b0010) ? and_result :
    (op == 4'b0011) ? or_result :
    (op == 4'b0100) ? xor_result :
    (op == 4'b0101) ? not_result :
    (op == 4'b0110) ? eq_result :
    (op == 4'b0111) ? lt_result :
    (op == 4'b1000) ? gt_result : {32{1'b0}};

// 零标志：结果全为0时置1
assign zero = (result == 32'd0) ? 1'b1 : 1'b0;

// 溢出标志：仅对算术运算有效，使用符号位和进位位判断
// 对于加法：溢出当 a 和 b 同号，但结果与之异号
wire a_sign = a[31];
wire b_sign = b[31];
wire res_sign = result[31];
wire add_carry = (add_result[32] == 1'b1); // 假设加法结果有33位，第32位是进位
wire sub_carry = (sub_result[32] == 1'b1); // 减法的借位

// 加法溢出：同号相加，结果符号相反
wire add_overflow = (a_sign == b_sign) && (a_sign != res_sign);
// 减法溢出：异号相减，结果符号与被减数相反（等价于 a - b 的溢出）
// 实际上，减法溢出条件：a_sign != b_sign 且 a_sign != res_sign
wire sub_overflow = (a_sign != b_sign) && (a_sign != res_sign);

// 溢出标志仅在ADD/SUB时有效，其他操作为0
assign overflow = 
    (op == 4'b0000) ? add_overflow :
    (op == 4'b0001) ? sub_overflow :
    1'b0;

endmodule