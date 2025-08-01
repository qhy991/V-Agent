output reg  [31:0] result,
output reg        zero

module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output reg  [31:0] result,
    output reg        zero
);

// 内部信号声明
reg [31:0] add_result;
reg [31:0] sub_result;

// 计算加法和减法结果
always_comb begin
    add_result = a + b;
    sub_result = a - b;
end

// 根据操作码选择结果并设置zero标志
always_comb begin
    case (op)
        4'b0000: result = add_result;
        4'b0001: result = sub_result;
        default: result = 32'b0;
    endcase

    // 设置zero标志：当result为全0时，zero为1
    zero = (result == 32'b0) ? 1'b1 : 1'b0;
end

endmodule