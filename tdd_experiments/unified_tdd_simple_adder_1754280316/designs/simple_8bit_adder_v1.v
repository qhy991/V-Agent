module simple_8bit_adder (
    input        clk,
    input        rst,
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output reg [7:0] sum,
    output reg       cout
);

    reg [8:0] temp_sum;

    always @(posedge clk) begin
        if (rst) begin
            sum <= 8'b0;
            cout <= 1'b0;
        end else begin
            temp_sum <= {1'b0, a} + {1'b0, b} + cin;
            sum <= temp_sum[7:0];
            cout <= temp_sum[8];
        end
    end

endmodule