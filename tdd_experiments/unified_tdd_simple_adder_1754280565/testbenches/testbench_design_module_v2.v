`timescale 1ns/1ps

module tb_design_module;

    // Testbench signals
    reg clk;
    reg rst_n;
    reg [7:0] data_in;
    wire [7:0] data_out;

    // Instantiate the design module
    design_module uut (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(data_in),
        .data_out(data_out)
    );

    // Clock generation
    always #5 clk = ~clk;  // 10ns clock period

    // Test sequence
    integer i;
    integer test_count;
    integer pass_count;

    // Monitor signals
    initial begin
        $monitor("Time=%0t: clk=%b, rst_n=%b, data_in=%0h, data_out=%0h", 
                 $time, clk, rst_n, data_in, data_out);
    end

    // Waveform dump
    initial begin
        $dumpfile("design_module.vcd");
        $dumpvars(0, tb_design_module);
    end

    // Test procedure for basic functionality
    task basic_functionality_test;
        begin
            $display("Starting basic functionality test at time %0t", $time);
            
            // Apply test vectors
            data_in = 8'h00; rst_n = 1; #10;
            data_in = 8'h55; rst_n = 1; #10;
            data_in = 8'hAA; rst_n = 1; #10;
            data_in = 8'hFF; rst_n = 1; #10;
            data_in = 8'h7F; rst_n = 1; #10;
            data_in = 8'h80; rst_n = 1; #10;
            
            // Check results
            if (data_out == 8'h00) pass_count = pass_count + 1;
            else $display("ERROR: Expected 8'h00, got %0h", data_out);
            
            if (data_out == 8'h55) pass_count = pass_count + 1;
            else $display("ERROR: Expected 8'h55, got %0h", data_out);
            
            if (data_out == 8'hAA) pass_count = pass_count + 1;
            else $display("ERROR: Expected 8'hAA, got %0h", data_out);
            
            if (data_out == 8'hFF) pass_count = pass_count + 1;
            else $display("ERROR: Expected 8'hFF, got %0h", data_out);
            
            if (data_out == 8'h7F) pass_count = pass_count + 1;
            else $display("ERROR: Expected 8'h7F, got %0h", data_out);
            
            if (data_out == 8'h80) pass_count = pass_count + 1;
            else $display("ERROR: Expected 8'h80, got %0h", data_out);
            
            $display("Basic functionality test completed at time %0t", $time);
        end
    endtask

    // Test procedure for reset functionality
    task reset_test;
        begin
            $display("Starting reset test at time %0t", $time);
            
            // Normal operation
            data_in = 8'h55; rst_n = 1; #10;
            data_in = 8'hAA; rst_n = 1; #10;
            
            // Assert reset
            rst_n = 0; #10;
            
            // After reset, output should be 0
            if (data_out == 8'h00) pass_count = pass_count + 1;
            else $display("ERROR: Reset failed, expected 8'h00, got %0h", data_out);
            
            // Deassert reset
            rst_n = 1; #10;
            
            // Output should be last value before reset
            if (data_out == 8'hAA) pass_count = pass_count + 1;
            else $display("ERROR: After reset, expected 8'hAA, got %0h", data_out);
            
            $display("Reset test completed at time %0t", $time);
        end
    endtask

    // Test procedure for edge cases
    task edge_case_test;
        begin
            $display("Starting edge case test at time %0t", $time);
            
            // Test all zero pattern
            data_in = 8'h00; rst_n = 1; #10;
            if (data_out == 8'h00) pass_count = pass_count + 1;
            else $display("ERROR: All zero pattern failed, got %0h", data_out);
            
            // Test all one pattern
            data_in = 8'hFF; rst_n = 1; #10;
            if (data_out == 8'hFF) pass_count = pass_count + 1;
            else $display("ERROR: All one pattern failed, got %0h", data_out);
            
            // Test alternating pattern
            data_in = 8'h55; rst_n = 1; #10;
            if (data_out == 8'h55) pass_count = pass_count + 1;
            else $display("ERROR: Alternating pattern failed, got %0h", data_out);
            
            data_in = 8'hAA; rst_n = 1; #10;
            if (data_out == 8'hAA) pass_count = pass_count + 1;
            else $display("ERROR: Alternating pattern failed, got %0h", data_out);
            
            // Test boundary values
            data_in = 8'h7F; rst_n = 1; #10;
            if (data_out == 8'h7F) pass_count = pass_count + 1;
            else $display("ERROR: Boundary value 7F failed, got %0h", data_out);
            
            data_in = 8'h80; rst_n = 1; #10;
            if (data_out == 8'h80) pass_count = pass_count + 1;
            else $display("ERROR: Boundary value 80 failed, got %0h", data_out);
            
            $display("Edge case test completed at time %0t", $time);
        end
    endtask

    // Main test sequence
    initial begin
        // Initialize signals
        clk = 0;
        rst_n = 0;
        data_in = 8'h00;
        
        // Initialize counters
        test_count = 0;
        pass_count = 0;
        
        // Wait for reset to stabilize
        #20;
        
        // Start tests
        basic_functionality_test();
        test_count = test_count + 1;
        
        reset_test();
        test_count = test_count + 1;
        
        edge_case_test();
        test_count = test_count + 1;
        
        // Run additional cycles to verify stability
        for (i=0; i<100; i=i+1) begin
            #10;
        end
        
        // Final report
        $display("Test Summary:");
        $display("Total Tests: %0d", test_count);
        $display("Passed Tests: %0d", pass_count);
        $display("Test Result: %s", (pass_count == test_count) ? "PASSED" : "FAILED");
        
        if (pass_count == test_count) begin
            $display("All tests passed successfully!");
        end else begin
            $display("Some tests failed!");
        end
        
        $finish;
    end

endmodule