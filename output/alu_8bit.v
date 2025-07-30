module alu_8bit(
    input wire [7:0] a,
    input wire [7:0] b,
    input wire [2:0] op,
    output reg [7:0] result,
    output reg zero_flag,
    output reg overflow_flag
);

// 操作码定义
localparam ADD = 3'b000;
localparam SUB = 3'b001;
localparam AND = 3'b010;
localparam OR  = 3'b011;
localparam XOR = 3'b100;

always @(*) begin
    case (op)
        ADD: begin
            result = a + b;
            overflow_flag = (a[7] == b[7]) && (result[7] != a[7]);
        end
        SUB: begin
            result = a - b;
            overflow_flag = (a[7] != b[7]) && (result[7] == b[7]);
        end
        AND: begin
            result = a & b;
            overflow_flag = 1'b0;
        end
        OR: begin
            result = a | b;
            overflow_flag = 1'b0;
        end
        XOR: begin
            result = a ^ b;
            overflow_flag = 1'b0;
        end
        default: begin
            result = 8'b0;
            overflow_flag = 1'b0;
        end
    endcase

    zero_flag = (result == 8'b0);
end

endmodule