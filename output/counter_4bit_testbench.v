module counter_4bit_testbench;

    reg clk;
    reg rst_n;
    reg en;
    wire [3:0] count;

    // Instantiate the counter module
    counter_4bit uut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .count(count)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns period clock
    end

    // Test sequence
    initial begin
        // Initialize signals
        rst_n = 0;
        en = 0;
        #20;

        // Release reset
        rst_n = 1;
        #10;

        // Enable counting
        en = 1;
        #100; // 100ns to count from 0 to 15

        // Disable counting
        en = 0;
        #20;

        // Check if count is still 15
        $display("Final count value: %b", count);
        #10;

        // Reset the counter
        rst_n = 0;
        #20;
        rst_n = 1;
        #10;

        // Finish simulation
        $finish;
    end

endmodule