module counter_tb;
    reg clk;
    reg rst_n;
    reg en;
    wire [7:0] count;

    counter uut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .count(count)
    );

    initial begin
        $dumpfile("counter.vcd");
        $dumpvars(1, counter_tb);

        clk = 0;
        rst_n = 0;
        en = 0;

        #10 rst_n = 1;
        #10 en = 1;
        #100 en = 0;
        #100 en = 1;
        #100 $finish;
    end

    always #5 clk = ~clk;
endmodule