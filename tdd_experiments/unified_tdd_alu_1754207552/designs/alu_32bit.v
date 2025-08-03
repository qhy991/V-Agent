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
reg [WIDTH-1:0] carry_in;
reg [WIDTH-1:0] carry_out;
reg [WIDTH-1:0] adder_result;
reg [WIDTH-1:0] not_b;

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

// always block for sequential logic
always @(posedge clk or posedge rst) begin
    if (rst) begin
        result <= '0;
        zero <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // 处理操作码
        case (op)
            OP_ADD: begin
                // ADD: a + b
                {carry_out[WIDTH-1], adder_result} = a + b;
                alu_result = adder_result;
                overflow = (a[WIDTH-1] == b[WIDTH-1]) && (adder_result[WIDTH-1] != a[WIDTH-1]);
            end

            OP_SUB: begin
                // SUB: a - b = a + (~b) + 1
                not_b = ~b;
                {carry_out[WIDTH-1], adder_result} = a + not_b + 1;
                alu_result = adder_result;
                overflow = (a[WIDTH-1] != b[WIDTH-1]) && (adder_result[WIDTH-1] != a[WIDTH-1]);
            end

            OP_AND: begin
                // AND: a & b
                alu_result = a & b;
                overflow = 1'b0;
            end

            OP_OR: begin
                // OR: a | b
                alu_result = a | b;
                overflow = 1'b0;
            end

            OP_XOR: begin
                // XOR: a ^ b
                alu_result = a ^ b;
                overflow = 1'b0;
            end

            OP_NOT: begin
                // NOT: ~a
                alu_result = ~a;
                overflow = 1'b0;
            end

            OP_EQ: begin
                // EQ: a == b
                alu_result = (a == b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end

            OP_LT: begin
                // LT: a < b (signed)
                alu_result = (a < b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end

            OP_GT: begin
                // GT: a > b (signed)
                alu_result = (a > b) ? 32'd1 : 32'd0;
                overflow = 1'b0;
            end

            default: begin
                alu_result = '0;
                overflow = 1'b0;
            end
        endcase

        // 更新输出
        result <= alu_result;
        zero <= (alu_result == 32'd0) ? 1'b1 : 1'b0;
    end
end

endmodule