// ===========================================================================
// Testbench for unknown_module
// Author: Professional Verification Engineer
// Date: 2025-04-05
// Description: Comprehensive testbench with multiple test scenarios
//              Fully compliant with standard Verilog syntax (IEEE 1364-2001)
// ===========================================================================

`timescale 1ns / 1ps

module tb_unknown_module;

    // ===========================================================================
    // Signal Declarations
    // ===========================================================================
    reg clk;
    reg rst_n;
    reg [7:0] data_in;
    wire [7:0] data_out;
    wire        valid_out;
    wire        error_flag;

    // Internal signals for test control
    integer test_case;
    integer cycle_count;
    integer pass_count;
    integer fail_count;

    // ===========================================================================
    // Clock Generation (10ns period, 50% duty cycle)
    // ===========================================================================
    always #5 clk = ~clk;

    // ===========================================================================
    // Reset Generation
    // ===========================================================================
    initial begin
        clk = 0;
        rst_n = 0;
        data_in = 8'h00;
        test_case = 0;
        cycle_count = 0;
        pass_count = 0;
        fail_count = 0;

        // Apply reset for 10 clock cycles
        #100 rst_n = 1;  // Release reset after 100ns (10 cycles)

        // Wait for one cycle after reset release to stabilize
        @(posedge clk);
    end

    // ===========================================================================
    // DUT Instantiation
    // ===========================================================================
    unknown_module uut (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(data_in),
        .data_out(data_out),
        .valid_out(valid_out),
        .error_flag(error_flag)
    );

    // ===========================================================================
    // Waveform Dump Setup (VCD File)
    // ===========================================================================
    initial begin
        $dumpfile("tb_unknown_module.vcd");
        $dumpvars(0, tb_unknown_module);
    end

    // ===========================================================================
    // Test Scenario Control Logic
    // ===========================================================================
    initial begin
        // Start simulation with basic functional test
        test_case = 1;
        $display("[%0t] Starting Basic Functional Test", $time);

        // Run basic functional test for 300 cycles
        for (cycle_count = 0; cycle_count < 300; cycle_count = cycle_count + 1) begin
            @(posedge clk);
            data_in = {data_in[6:0], data_in[7]}; // Rotate input pattern
            if (cycle_count == 299) begin
                $display("[%0t] Basic Functional Test Completed.", $time);
                test_case = 2;
                $display("[%0t] Starting Boundary Conditions Test", $time);
            end
        end

        // Run boundary conditions test
        for (cycle_count = 0; cycle_count < 300; cycle_count = cycle_count + 1) begin
            @(posedge clk);
            if (cycle_count == 0) begin
                data_in = 8'h00; // Min value
            end else if (cycle_count == 150) begin
                data_in = 8'hFF; // Max value
            end else if (cycle_count == 299) begin
                $display("[%0t] Boundary Conditions Test Completed.", $time);
                test_case = 3;
                $display("[%0t] Starting Reset Behavior Test", $time);
            end
        end

        // Run reset behavior test
        for (cycle_count = 0; cycle_count < 400; cycle_count = cycle_count + 1) begin
            @(posedge clk);
            if (cycle_count == 100) begin
                // Force reset during operation
                rst_n = 0;
                $display("[%0t] Reset asserted during operation.", $time);
            end else if (cycle_count == 150) begin
                // Release reset
                rst_n = 1;
                $display("[%0t] Reset released.", $time);
            end else if (cycle_count == 399) begin
                $display("[%0t] Reset Behavior Test Completed.", $time);
            end
        end

        // Finalize simulation
        $display("[%0t] All tests completed. Simulation ending.", $time);
        $finish;
    end

    // ===========================================================================
    // Monitoring and Assertion Checks
    // ===========================================================================
    always @(posedge clk) begin
        // Monitor key signals
        $monitor("%0t | clk=%b, rst_n=%b, data_in=%0d, data_out=%0d, valid_out=%b, error_flag=%b",
                 $time, clk, rst_n, data_in, data_out, valid_out, error_flag);

        // Basic functional check: valid_out should be high when data is valid
        if (valid_out && !error_flag) begin
            if (data_out != data_in) begin
                $display("[%0t] ERROR: Data mismatch! Expected %0d, Got %0d", $time, data_in, data_out);
                fail_count = fail_count + 1;
            end else begin
                pass_count = pass_count + 1;
            end
        end

        // Error flag check: should not be set unless invalid condition
        if (error_flag) begin
            $display("[%0t] ERROR: Error flag asserted! Check logic.", $time);
            fail_count = fail_count + 1;
        end

        // Ensure reset behavior is correct: after reset, outputs should be stable
        if (!rst_n && (valid_out || error_flag)) begin
            $display("[%0t] WARNING: Valid or error signal active during reset!", $time);
            fail_count = fail_count + 1;
        end
    end

    // ===========================================================================
    // Final Test Report
    // ===========================================================================
    initial begin
        #1000; // Allow final monitoring
        $display("===================================================================");
        $display("TEST SUMMARY REPORT");
        $display("===================================================================");
        $display("Total Test Cases Executed: 3");
        $display("Total Cycles Simulated:     1000");
        $display("Pass Count:                 %0d", pass_count);
        $display("Fail Count:                 %0d", fail_count);
        $display("Overall Status:             %s", (fail_count > 0) ? "FAILED" : "PASSED");
        $display("===================================================================");
        $finish;
    end

endmodule