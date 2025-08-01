module correct_tb;
    reg clk;
    wire [7:0] count;

    // Instantiate the module under test
    correct uut (
        .clk(clk),
        .count(count)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns period clock
    end

    // Test sequence
    initial begin
        $dumpfile("correct_tb.vcd");
        $dumpvars(0, correct_tb);

        // Test case 1: Basic functionality
        #10;
        $display("Test Case 1: Basic Functionality");
        $display("Expected: count = 8'h00");
        $display("Actual:   count = %d", count);
        if (count != 8'h00) $display("Test Failed: count is not 8'h00");
        else $display("Test Passed: count is 8'h00");

        // Test case 2: After 10ns, count should be 8'hFF
        #10;
        $display("Test Case 2: After 10ns, count should be 8'hFF");
        $display("Expected: count = 8'hFF");
        $display("Actual:   count = %d", count);
        if (count != 8'hFF) $display("Test Failed: count is not 8'hFF");
        else $display("Test Passed: count is 8'hFF");

        // Test case 3: Display message and finish after 10ns
        #10;
        $display("Test Case 3: Display message and finish");
        $display("Expected: Success: count = 255");
        $display("Actual:   Success: count = %d", count);
        if (count != 8'hFF) $display("Test Failed: count is not 8'hFF");
        else $display("Test Passed: count is 8'hFF");

        // Test case 4: Boundary condition - max value
        #10;
        $display("Test Case 4: Boundary Condition - Max Value (8'hFF)");
        $display("Expected: count = 8'hFF");
        $display("Actual:   count = %d", count);
        if (count != 8'hFF) $display("Test Failed: count is not 8'hFF");
        else $display("Test Passed: count is 8'hFF");

        // Test case 5: Random test - simulate a few cycles
        #10;
        $display("Test Case 5: Random Test - Simulate a few cycles");
        $display("Expected: count remains 8'hFF");
        $display("Actual:   count = %d", count);
        if (count != 8'hFF) $display("Test Failed: count changed from 8'hFF");
        else $display("Test Passed: count remains 8'hFF");

        $finish;
    end
endmodule