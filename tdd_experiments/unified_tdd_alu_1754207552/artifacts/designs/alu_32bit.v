module alu_32bit #(
    parameter WIDTH = 32
) (
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    input  logic [3:0]      op,
    output logic [WIDTH-1:0] result,
    output logic            zero,
    output logic            overflow
);

// 内部信号声明
logic [WIDTH-1:0] add_result;
logic [WIDTH-1:0] sub_result;
logic [WIDTH-1:0] and_result;
logic [WIDTH-1:0] or_result;
logic [WIDTH-1:0] xor_result;
logic [WIDTH-1:0] not_result;
logic [WIDTH-1:0] eq_result;
logic [WIDTH-1:0] lt_result;
logic [WIDTH-1:0] gt_result;

// 组合逻辑实现：算术运算
assign add_result = a + b;
assign sub_result = a - b;

// 组合逻辑实现：逻辑运算
assign and_result = a & b;
assign or_result  = a | b;
assign xor_result = a ^ b;
assign not_result = ~a;

// 组合逻辑实现：比较运算（结果为32位，仅最高位有效）
assign eq_result = (a == b) ? {WIDTH{1'b1}} : {WIDTH{1'b0}};
assign lt_result = (a < b) ? {WIDTH{1'b1}} : {WIDTH{1'b0}};
assign gt_result = (a > b) ? {WIDTH{1'b1}} : {WIDTH{1'b0}};

// 溢出标志计算（仅对加法和减法有效）
// 加法溢出：符号位相同但结果符号不同
logic a_sign, b_sign, result_sign;
assign a_sign = a[WIDTH-1];
assign b_sign = b[WIDTH-1];
assign result_sign = add_result[WIDTH-1];

// 加法溢出：(a_sign == b_sign) && (a_sign != result_sign)
logic add_overflow;
assign add_overflow = (a_sign == b_sign) && (a_sign != result_sign);

// 减法溢出：等价于 a + (-b)，即 a + (~b + 1)
// 可简化为：(a_sign != b_sign) && (a_sign != result_sign)
logic sub_overflow;
assign sub_overflow = (a_sign != b_sign) && (a_sign != result_sign[WIDTH-1]);

// 溢出标志：仅在ADD/SUB时生效，其他操作为0
assign overflow = (op == 4'b0000 || op == 4'b0001) ? 
                  (op == 4'b0000 ? add_overflow : sub_overflow) : 1'b0;

// 零标志：结果全为0则置1
assign zero = (result == 0) ? 1'b1 : 1'b0;

// 根据操作码选择输出结果
always @(*) begin
    case (op)
        4'b0000: result = add_result;   // ADD
        4'b0001: result = sub_result;   // SUB
        4'b0010: result = and_result;   // AND
        4'b0011: result = or_result;    // OR
        4'b0100: result = xor_result;   // XOR
        4'b0101: result = not_result;   // NOT
        4'b0110: result = eq_result;    // EQ
        4'b0111: result = lt_result;    // LT
        4'b1000: result = gt_result;    // GT
        default: result = 32'd0;        // 默认值
    endcase
end

endmodule