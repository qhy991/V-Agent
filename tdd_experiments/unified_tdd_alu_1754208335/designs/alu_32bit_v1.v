module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output wire [31:0] result,
    output wire       zero
);

// 内部信号声明
wire [31:0] add_result;
wire [31:0] sub_result;
wire [31:0] and_result;
wire [31:0] or_result;
wire [31:0] xor_result;
wire [31:0] sll_result;
wire [31:0] srl_result;

// 组合逻辑实现：根据操作码选择对应运算
assign add_result = a + b;
assign sub_result = a - b;
assign and_result = a & b;
assign or_result  = a | b;
assign xor_result = a ^ b;
assign sll_result = {a << b[4:0]};
assign srl_result = {a >> b[4:0]};

// 多路选择器：根据op选择输出结果
assign result = (op == 4'b0000) ? add_result :
                (op == 4'b0001) ? sub_result :
                (op == 4'b0010) ? and_result :
                (op == 4'b0011) ? or_result :
                (op == 4'b0100) ? xor_result :
                (op == 4'b0101) ? sll_result :
                (op == 4'b0110) ? srl_result :
                                 32'd0;

// 零标志：当result为0时置1
assign zero = (result == 32'd0);

endmodule