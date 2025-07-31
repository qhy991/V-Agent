module simple_and_tb;

    // Inputs
    reg clk;
    reg rst_n;

    // Outputs
    wire [7:0] data;

    // Instantiate the Unit Under Test (UUT)
    simple_and uut (
        .clk(clk),
        .rst_n(rst_n),
        .data(data)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns period
    end

    // Test sequence
    initial begin
        $dumpfile("simple_and_tb.vcd");
        $dumpvars(0, simple_and_tb);

        // Initialize inputs
        rst_n = 0;
        #20;

        // Test case 1: Reset and normal operation
        $display("\n=== Test Case 1: Reset and Normal Operation ===");
        rst_n = 1;
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);

        // Test case 2: Boundary condition (max value)
        $display("\n=== Test Case 2: Boundary Condition (Max Value) ===");
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);

        // Test case 3: Random test (incrementing pattern)
        $display("\n=== Test Case 3: Random Test (Incrementing Pattern) ===");
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);

        // Test case 4: Reset during operation
        $display("\n=== Test Case 4: Reset During Operation ===");
        rst_n = 0;
        #10;
        $display("Time %t: data = %b", $time, data);
        rst_n = 1;
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);
        #10;
        $display("Time %t: data = %b", $time, data);

        // Finish simulation
        #10;
        $display("\n=== Simulation Finished ===");
        $finish;
    end

endmodule