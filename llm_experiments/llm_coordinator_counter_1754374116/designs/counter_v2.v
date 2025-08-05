module counter(
    input        clk,
    input        rst,
    input        en,
    input        load,
    input  [7:0] data_in,
    output reg   carry,
    output reg   zero,
    output reg [7:0] count
);

    // Internal signal declaration
    reg [7:0] next_count;

    // Sequential logic with asynchronous reset
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            count  <= 8'd0;
            carry  <= 1'b0;
            zero   <= 1'b1;
        end else begin
            count  <= next_count;
            carry  <= (next_count == 8'hFF) ? 1'b1 : 1'b0;
            zero   <= (next_count == 8'd0) ? 1'b1 : 1'b0;
        end
    end

    // Combinational logic for next state
    always @(*) begin
        if (load)
            next_count = data_in;
        else if (en)
            next_count = count + 8'd1;
        else
            next_count = count;
    end

endmodule