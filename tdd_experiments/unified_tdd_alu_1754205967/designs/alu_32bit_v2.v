module alu_32bit (
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0] op,
    output reg [31:0] result,
    output reg zero,
    output reg overflow
);

always @(*) begin
    case (op)
        4'b0000: begin // ADD
            {overflow, result} = a + b;
            zero = (result == 0);
        end
        4'b0001: begin // SUB
            {overflow, result} = a - b;
            zero = (result == 0);
        end
        4'b0010: begin // AND
            result = a & b;
            zero = (result == 0);
            overflow = 1'b0;
        end
        4'b0011: begin // OR
            result = a | b;
            zero = (result == 0);
            overflow = 1'b0;
        end
        4'b0100: begin // XOR
            result = a ^ b;
            zero = (result == 0);
            overflow = 1'b0;
        end
        4'b0101: begin // NOT
            result = ~a;
            zero = (result == 0);
            overflow = 1'b0;
        end
        4'b0110: begin // EQ
            result = (a == b) ? 32'd1 : 32'd0;
            zero = (result == 0);
            overflow = 1'b0;
        end
        4'b0111: begin // LT
            result = (a < b) ? 32'd1 : 32'd0;
            zero = (result == 0);
            overflow = 1'b0;
        end
        4'b1000: begin // GT
            result = (a > b) ? 32'd1 : 32'd0;
            zero = (result == 0);
            overflow = 1'b0;
        end
        default: begin
            result = 32'd0;
            zero = 1'b1;
            overflow = 1'b0;
        end
    endcase
end

endmodule