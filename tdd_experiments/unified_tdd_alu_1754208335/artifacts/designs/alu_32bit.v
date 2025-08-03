module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output [31:0] result,
    output        zero
);

    wire [31:0] internal_result;
    assign zero = (internal_result == 32'd0);

    always @(*) begin
        case (op)
            4'b0000: internal_result = a + b;
            4'b0001: internal_result = a - b;
            4'b0010: internal_result = a & b;
            4'b0011: internal_result = a | b;
            4'b0100: internal_result = a ^ b;
            4'b0101: internal_result = a << b[4:0];
            4'b0110: internal_result = a >> b[4:0];
            default: internal_result = 32'd0;
        endcase
    end

    assign result = internal_result;

endmodule