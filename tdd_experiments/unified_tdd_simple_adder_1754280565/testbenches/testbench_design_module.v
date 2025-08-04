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

    // Testbench initial block
    initial begin
        // Initialize signals
        clk = 0;
        rst_n = 0;
        data_in = 8'h0;

        // Start simulation
        $display("=== Design Module Testbench Started ===");
        $dumpfile("design_module.vcd");
        $dumpvars(0, tb_design_module);

        // Run basic functionality test
        basic_functionality_test();

        // Run reset test
        reset_test();

        // Run boundary conditions test
        boundary_conditions_test();

        // Finish simulation
        $display("=== All Tests Completed ===");
        $finish;
    end

    // Basic functionality test
    task basic_functionality_test;
        integer i;
        
        $display("Starting basic functionality test...");
        
        // Apply reset
        rst_n = 0;
        #10;
        
        // Release reset
        rst_n = 1;
        #10;
        
        // Test various data values
        for (i = 0; i < 10; i = i + 1) begin
            data_in = i * 25;
            #10;
            if (data_out !== data_in) begin
                $display("ERROR: Data mismatch at cycle %0d. Expected: %h, Got: %h", 
                         i, data_in, data_out);
            end else begin
                $display("PASS: Data transfer successful. Input: %h, Output: %h", 
                         data_in, data_out);
            end
        end
        
        // Test with random data
        for (i = 0; i < 5; i = i + 1) begin
            data_in = $random % 256;
            #10;
            if (data_out !== data_in) begin
                $display("ERROR: Random data mismatch at cycle %0d. Expected: %h, Got: %h", 
                         i, data_in, data_out);
            end else begin
                $display("PASS: Random data transfer successful. Input: %h, Output: %h", 
                         data_in, data_out);
            end
        end
        
        $display("Basic functionality test completed.");
    endtask

    // Reset test
    task reset_test;
        integer i;
        
        $display("Starting reset test...");
        
        // Apply reset and verify output is zero
        rst_n = 0;
        data_in = 8'hFF;
        #10;
        
        if (data_out !== 8'h0) begin
            $display("ERROR: Reset failed. Output should be 0 but got %h", data_out);
        end else begin
            $display("PASS: Reset successful. Output is %h as expected", data_out);
        end
        
        // Release reset and check normal operation
        rst_n = 1;
        data_in = 8'hAA;
        #10;
        
        if (data_out !== 8'hAA) begin
            $display("ERROR: Normal operation failed after reset. Expected: AA, Got: %h", data_out);
        end else begin
            $display("PASS: Normal operation resumed after reset. Output: %h", data_out);
        end
        
        // Test multiple resets
        for (i = 0; i < 3; i = i + 1) begin
            rst_n = 0;
            #10;
            rst_n = 1;
            #10;
            if (data_out !== 8'h0) begin
                $display("ERROR: Reset %0d failed. Output should be 0 but got %h", 
                         i, data_out);
            end else begin
                $display("PASS: Reset %0d successful", i);
            end
        end
        
        $display("Reset test completed.");
    endtask

    // Boundary conditions test
    task boundary_conditions_test;
        integer i;
        
        $display("Starting boundary conditions test...");
        
        // Apply reset
        rst_n = 0;
        #10;
        rst_n = 1;
        #10;
        
        // Test minimum value
        data_in = 8'h00;
        #10;
        if (data_out !== 8'h00) begin
            $display("ERROR: Minimum value test failed. Expected: 00, Got: %h", data_out);
        end else begin
            $display("PASS: Minimum value test passed. Input: %h, Output: %h", 
                     data_in, data_out);
        end
        
        // Test maximum value
        data_in = 8'hFF;
        #10;
        if (data_out !== 8'hFF) begin
            $display("ERROR: Maximum value test failed. Expected: FF, Got: %h", data_out);
        end else begin
            $display("PASS: Maximum value test passed. Input: %h, Output: %h", 
                     data_in, data_out);
        end
        
        // Test all bit patterns
        for (i = 0; i < 256; i = i + 1) begin
            data_in = i;
            #10;
            if (data_out !== i) begin
                $display("ERROR: Bit pattern test failed at value %0d. Expected: %h, Got: %h", 
                         i, i, data_out);
            end
        end
        
        $display("Boundary conditions test completed.");
    endtask

    // Monitor for debugging
    initial begin
        $monitor("Time=%0t: clk=%b, rst_n=%b, data_in=%h, data_out=%h", 
                 $time, clk, rst_n, data_in, data_out);
    end

endmodule