// File: testbench_counter.v
// Description: Testbench for counter module
// Fixed: 2025-08-08

`timescale 1ns/1ps

module testbench_counter;

// Parameters
parameter WIDTH = 4;
parameter DIRECTION = 1'b1;

// Test signals
reg clk;
reg rst_n;
reg enable;
wire [WIDTH-1:0] count;

// Test statistics
integer passed_tests = 0;
integer failed_tests = 0;
integer test_count = 0;

// DUT instance
counter #(
    .WIDTH(WIDTH),
    .DIRECTION(DIRECTION)
) dut (
    .clk(clk),
    .rst_n(rst_n),
    .enable(enable),
    .count(count)
);

// Clock generation
always begin
    #5 clk = ~clk;
end

// Test results display
task display_test_results;
begin
    $display("========================================");
    $display("Test Summary:");
    $display("Total Tests: %0d", test_count);
    $display("Passed: %0d", passed_tests);
    $display("Failed: %0d", failed_tests);
    $display("Pass Rate: %0.2f%%", (passed_tests*100.0)/test_count);
    $display("========================================");
end
endtask

// Test case 1: Basic functionality test
task test_basic_functionality;
begin
    test_count = test_count + 1;
    $display("[Test %0d] Starting basic functionality test", test_count);
    
    // Initialize signals
    clk = 1'b0;
    rst_n = 1'b0;
    enable = 1'b1;
    
    // Release reset
    #10 rst_n = 1'b1;
    
    // Wait for some cycles and check counting
    integer i;
    for (i = 0; i < 15; i = i + 1) begin
        #10;
        if (count === i+1) begin
            $display("Count value %0d at %0d ps matches expected value", count, $time);
        end else begin
            $display("Error: Count value %0d at %0d ps does not match expected value %0d", count, $time, i+1);
            failed_tests = failed_tests + 1;
            break;
        end
    end
    
    if (count === 15) begin
        $display("[Test %0d] Basic functionality test passed", test_count);
        passed_tests = passed_tests + 1;
    end else begin
        $display("[Test %0d] Basic functionality test failed", test_count);
    end
    
    // Reset for next test
    rst_n = 1'b0;
    #10 rst_n = 1'b1;
end
endtask

// Test case 2: Reset functionality test
task test_reset_functionality;
begin
    test_count = test_count + 1;
    $display("[Test %0d] Starting reset functionality test", test_count);
    
    // Initialize signals
    clk = 1'b0;
    rst_n = 1'b0;
    enable = 1'b1;
    
    // Hold reset
    #5 clk = 1'b1;
    #10 clk = 1'b0;
    
    if (count === 0) begin
        $display("[Test %0d] Counter held at reset correctly initialized to 0", test_count);
    end else begin
        $display("Error: Counter did not initialize to 0 during reset. Current value: %0d", count);
        failed_tests = failed_tests + 1;
    end
    
    // Release reset
    rst_n = 1'b1;
    #10;
    
    if (count === 1) begin
        $display("[Test %0d] Counter resumed counting after reset", test_count);
        passed_tests = passed_tests + 1;
    end else begin
        $display("Error: Counter did not start counting after reset. Current value: %0d", count);
    end
end
endtask

// Test case 3: Direction functionality test (down counter)
task test_down_counter;
begin
    test_count = test_count + 1;
    $display("[Test %0d] Starting down counter functionality test", test_count);
    
    // Create a new instance with DIRECTION=0
    counter #(
        .WIDTH(WIDTH),
        .DIRECTION(1'b0)
    ) down_counter (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .count(count)
    );
    
    // Initialize signals
    clk = 1'b0;
    rst_n = 1'b0;
    enable = 1'b1;
    
    // Release reset
    #10 rst_n = 1'b1;
    
    // Wait for some cycles and check counting down
    integer i;
    for (i = 0; i < 15; i = i + 1) begin
        #10;
        if (count === 15-i) begin
            $display("Count value %0d at %0d ps matches expected down count value", count, $time);
        end else begin
            $display("Error: Count value %0d at %0d ps does not match expected down count value %0d", count, $time, 15-i);
            failed_tests = failed_tests + 1;
            break;
        end
    end
    
    if (count === 0) begin
        $display("[Test %0d] Down counter functionality test passed", test_count);
        passed_tests = passed_tests + 1;
    end else begin
        $display("[Test %0d] Down counter functionality test failed", test_count);
    end
    
    // Remove the down counter instance
    $deposit(down_counter, 1'bx);
end
endtask

// Test case 4: Enable functionality test
task test_enable_functionality;
begin
    test_count = test_count + 1;
    $display("[Test %0d] Starting enable functionality test", test_count);
    
    // Initialize signals
    clk = 1'b0;
    rst_n = 1'b0;
    enable = 1'b0;  // Disable counting
    
    // Release reset
    #10 rst_n = 1'b1;
    
    // Keep enable low and check if count stays at 0
    integer i;
    for (i = 0; i < 5; i = i + 1) begin
        #10 clk = 1'b1;
        #10 clk = 1'b0;
        if (count !== 0) begin
            $display("Error: Counter incremented when enable was low. Current value: %0d", count);
            failed_tests = failed_tests + 1;
            break;
        end
    end
    
    // Enable counting
    enable = 1'b1;
    #10 clk = 1'b1;
    #10 clk = 1'b0;
    
    if (count === 1) begin
        $display("[Test %0d] Enable functionality test passed", test_count);
        passed_tests = passed_tests + 1;
    end else begin
        $display("Error: Counter did not start counting when enable was asserted. Current value: %0d", count);
    end
end
endtask

// Test case 5: Width functionality test (8-bit)
task test_8bit_counter;
begin
    test_count = test_count + 1;
    $display("[Test %0d] Starting 8-bit counter functionality test", test_count);
    
    // Create a new instance with WIDTH=8
    counter #(
        .WIDTH(8),
        .DIRECTION(DIRECTION)
    ) wide_counter (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .count(count)
    );
    
    // Initialize signals
    clk = 1'b0;
    rst_n = 1'b0;
    enable = 1'b1;
    
    // Release reset
    #10 rst_n = 1'b1;
    
    // Wait for some cycles and check 8-bit counting
    integer i;
    for (i = 0; i < 255; i = i + 1) begin
        #10;
        if (count === i+1) begin
            $display("Count value %0d at %0d ps matches expected 8-bit value", count, $time);
        end else begin
            $display("Error: Count value %0d at %0d ps does not match expected 8-bit value %0d", count, $time, i+1);
            failed_tests = failed_tests + 1;
            break;
        end
    end
    
    if (count === 255) begin
        $display("[Test %0d] 8-bit counter functionality test passed", test_count);
        passed_tests = passed_tests + 1;
    end else begin
        $display("[Test %0d] 8-bit counter functionality test failed", test_count);
    end
    
    // Remove the wide counter instance
    $deposit(wide_counter, 1'bx);
end
endtask

// Test case 6: Edge case test (rollover)
task test_rollover;
begin
    test_count = test_count + 1;
    $display("[Test %0d] Starting rollover functionality test", test_count);
    
    // Initialize signals
    clk = 1'b0;
    rst_n = 1'b0;
    enable = 1'b1;
    
    // Release reset
    #10 rst_n = 1'b1;
    
    // Wait for rollover
    integer i;
    for (i = 0; i < 16; i = i + 1) begin
        #10;
        if (i < 15 && count === i+1) begin
            $display("Count value %0d at %0d ps matches expected value", count, $time);
        end else if (i == 15 && count === 0) begin
            $display("Count value %0d at %0d ps matches rollover value", count, $time);
        end else if (i == 15) begin
            $display("Error: Counter did not roll over correctly. Current value: %0d", count);
            failed_tests = failed_tests + 1;
            break;
        end
    end
    
    if (count === 0) begin
        $display("[Test %0d] Rollover functionality test passed", test_count);
        passed_tests = passed_tests + 1;
    end else begin
        $display("[Test %0d] Rollover functionality test failed", test_count);
    end
end
endtask

// Main test process
initial begin
    $display("========================================");
    $display("Counter Module Testbench");
    $display("Date: %0s", $time);
    $display("========================================");
    
    // Initialize signals
    clk = 1'b0;
    rst_n = 1'b0;
    enable = 1'b0;
    
    // Run tests
    test_basic_functionality();
    test_reset_functionality();
    test_down_counter();
    test_enable_functionality();
    test_8bit_counter();
    test_rollover();
    
    // Display final results
    display_test_results();
    
    // Finish simulation
    #20 $finish;
end

// Waveform dump
initial begin
    $dumpfile("counter_tb.vcd");
    $dumpvars(0, testbench_counter);
end

endmodule