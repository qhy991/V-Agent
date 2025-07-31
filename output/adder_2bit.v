module adder_2bit(
    input [1:0] a,
    input [1:0] b,
    input carry_in,
    output reg [2:0] sum,
    output reg carry_out
);

    always @(a, b, carry_in) begin
        {carry_out, sum} = a + b + carry_in;
    end

endmodule