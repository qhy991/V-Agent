module testbench_cpu();
    reg clk;
    reg rst_n;
    
    // DUT instance
    cpu uut (
        .clk(clk),
        .rst_n(rst_n)
    );
    
    // Clock generation
    always #5 clk = ~clk;
    
    // Test sequence
    initial begin
        clk = 0;
        rst_n = 0;
        #10 rst_n = 1;
        #1000 $finish;
    end
endmodule