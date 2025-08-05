module alu_8bit (
    input  [7:0] a,
    input  [7:0] b,
    input  [1:0] op,
    output [7:0] result,
    output       zero
);

    wire [7:0] add_result;
    wire [7:0] sub_result;
    wire [7:0] and_result;
    wire [7:0] or_result;

    // Basic operations
    assign add_result = a + b;
    assign sub_result = a - b;
    assign and_result = a & b;
    assign or_result = a | b;

    // Operation selection
    assign result = (op == 2'b00) ? add_result :
                    (op == 2'b01) ? sub_result :
                    (op == 2'b10) ? and_result :
                    (op == 2'b11) ? or_result : 8'h00;

    // Zero flag
    assign zero = (result == 8'h00);

endmodule