module cpu_tb;
    reg clk;
    reg rst_n;

    // Instantiate the DUT
    cpu uut (
        .clk(clk),
        .rst_n(rst_n)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns period clock
    end

    // Test sequence
    initial begin
        $dumpfile("cpu_tb.vcd");
        $dumpvars(0, cpu_tb);

        // Test case 1: Normal operation (reset released)
        rst_n = 0;
        #10;
        rst_n = 1;
        #20;
        $display("[TEST] Test Case 1: Normal operation - Reset released");

        // Test case 2: Reset active (asserted)
        rst_n = 0;
        #10;
        $display("[TEST] Test Case 2: Reset active");

        // Test case 3: Reset de-asserted after some time
        rst_n = 1;
        #20;
        $display("[TEST] Test Case 3: Reset de-asserted after delay");

        // Test case 4: Boundary condition - reset at edge of clock cycle
        rst_n = 0;
        #5;
        rst_n = 1;
        #5;
        $display("[TEST] Test Case 4: Reset at clock edge");

        // Test case 5: Random test (random reset sequence)
        rst_n = 0;
        #10;
        rst_n = 1;
        #5;
        rst_n = 0;
        #5;
        rst_n = 1;
        #10;
        $display("[TEST] Test Case 5: Random reset sequence");

        // End simulation
        #100;
        $finish;
    end
endmodule