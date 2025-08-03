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

// 加法运算：a + b
assign add_result = a + b;

// 减法运算：a - b
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
    (op == 4'b1000) ? gt_result :
                     {32{1'b0}};

// 零标志：结果全为0时置1
assign zero = (result == 32'd0) ? 1'b1 : 1'b0;

// 溢出标志：仅对加法和减法有效
// 加法溢出：符号位相同但结果符号位不同
// 减法溢出：等价于 a + (-b)，即加法溢出情况
wire a_sign = a[31];
wire b_sign = b[31];
wire result_sign = result[31];

// 加法溢出检测：a和b同号，但结果与之异号
wire add_overflow = (a_sign == b_sign) && (a_sign != result_sign);

// 减法溢出：a - b = a + (-b)，所以检查 a 和 (-b) 的符号
wire neg_b_sign = ~b_sign;
wire sub_overflow = (a_sign == neg_b_sign) && (a_sign != result_sign);

// 溢出标志：仅当操作为ADD或SUB时有效
assign overflow = (op == 4'b0000) ? add_overflow :
                  (op == 4'b0001) ? sub_overflow :
                                  1'b0;

endmodule