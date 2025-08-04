module alu_32bit (
    input        clk,
    input        rst,
    input  [31:0] a,
    input  [31:0] b,
    input  [3:0]  op,
    output reg [31:0] result,
    output reg zero
);

    always @(posedge clk) begin
        if (rst) begin
            result <= 32'b0;
            zero   <= 1'b0;
        end else begin
            case (op)
                4'b0000: result <= a + b;        // 加法
                4'b0001: result <= a - b;        // 减法
                4'b0010: result <= a & b;        // 逻辑与
                4'b0011: result <= a | b;        // 逻辑或
                4'b0100: result <= a ^ b;        // 异或
                4'b0101: result <= a << b[4:0];  // 逻辑左移
                4'b0110: result <= a >> b[4:0];  // 逻辑右移
                default: result <= 32'b0;        // 无效操作码
            endcase
            
            // 零标志位：当结果为0时置1
            zero <= (result == 32'b0) ? 1'b1 : 1'b0;
        end
    end

endmodule