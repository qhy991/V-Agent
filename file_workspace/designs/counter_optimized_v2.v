module counter (
    input      clk,
    input      rst_n,
    input      en,
    output reg [7:0] count
);

    // 使用异步复位、同步使能的计数器，减少控制逻辑复杂度
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'd0;
        else
            count <= count + en;  // 利用 en 作为加法的使能条件（0 或 1）
    end

endmodule