module alu_32bit #(
    parameter WIDTH = 32
) (
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input [3:0] op,
    output reg [WIDTH-1:0] result,
    output reg zero,
    output reg overflow
);

// 内部信号声明
reg [WIDTH-1:0] alu_result;
reg [WIDTH-1:0] temp_a, temp_b;
reg signed [WIDTH-1:0] signed_a, signed_b;
reg signed [WIDTH-1:0] sum;
reg carry_out;
reg sign_a, sign_b, sign_sum;

// 操作码定义
localparam OP_ADD   = 4'b0000;
localparam OP_SUB   = 4'b0001;
localparam OP_AND   = 4'b0010;
localparam OP_OR    = 4'b0011;
localparam OP_XOR   = 4'b0100;
localparam OP_NOT   = 4'b0101;
localparam OP_EQ    = 4'b0110;
localparam OP_LT    = 4'b0111;
localparam OP_GT    = 4'b1000;

// 时序逻辑：在时钟上升沿更新输出
always @(posedge clk or posedge rst) begin
    if (rst) begin
        result <= 32'd0;
        zero <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // 根据操作码执行相应运算
        case (op)
            OP_ADD: begin
                // 加法运算
                {carry_out, sum} = signed_a + signed_b;
                alu_result = sum;
                overflow = (sign_a == sign_b) && (sign_a != sign_sum);
            end

            OP_SUB: begin
                // 减法运算：a - b = a + (-b)
                {carry_out, sum} = signed_a + (~signed_b + 1);
                alu_result = sum;
                overflow = (sign_a != sign_b) && (sign_a != sign_sum);
            end

            OP_AND: begin
                alu_result = a & b;
                overflow = 1'b0;
            end

            OP_OR: begin
                alu_result = a | b;
                overflow = 1'b0;
            end

            OP_XOR: begin
                alu_result = a ^ b;
                overflow = 1'b0;
            end

            OP_NOT: begin
                alu_result = ~a;
                overflow = 1'b0;
            end

            OP_EQ: begin
                alu_result = (a == b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end

            OP_LT: begin
                alu_result = (signed_a < signed_b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end

            OP_GT: begin
                alu_result = (signed_a > signed_b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end

            default: begin
                alu_result = 32'd0;
                overflow = 1'b0;
            end
        endcase

        // 更新结果和标志位
        result <= alu_result;
        zero <= (alu_result == 32'd0) ? 1'b1 : 1'b0;

        // 仅在算术运算中更新溢出标志（ADD/SUB）
        // 其他运算的overflow保持为0，已在上面赋值
    end
end

// 用于算术运算的符号位提取
assign sign_a = a[WIDTH-1];
assign sign_b = b[WIDTH-1];
assign sign_sum = alu_result[WIDTH-1];

// 转换输入为有符号数以进行正确比较和溢出检测
assign signed_a = $signed(a);
assign signed_b = $signed(b);

endmodule