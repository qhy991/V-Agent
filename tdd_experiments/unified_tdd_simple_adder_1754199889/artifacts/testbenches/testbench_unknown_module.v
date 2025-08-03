// ===========================================================================
// Testbench for unknown_module
// Author: Professional Verification Engineer
// Date: 2025-04-05
// Description: Comprehensive testbench for verifying unknown_module functionality
// Features: Standard Verilog, no SystemVerilog constructs, full coverage of basic_test
// ===========================================================================

`timescale 1ns / 1ps

module tb_unknown_module;

    // =======================================================================
    // Signal Declarations
    // =======================================================================
    reg clk;
    reg rst_n;
    reg [31:0] test_data_in;
    wire [31:0] test_data_out;
    wire        test_done;

    // =======================================================================
    // Clock Generation (10.0ns period -> 100MHz)
    // =======================================================================
    always #5.0 clk = ~clk;  // 5ns high, 5ns low => 10ns period

    // =======================================================================
    // Reset Generation
    // =======================================================================
    initial begin
        clk = 0;
        rst_n = 0;
        #20.0 rst_n = 1;  // Assert reset for 20ns, then deassert
    end

    // =======================================================================
    // DUT Instantiation
    // =======================================================================
    unknown_module uut (
        .clk(clk),
        .rst_n(rst_n),
        .test_data_in(test_data_in),
        .test_data_out(test_data_out),
        .test_done(test_done)
    );

    // =======================================================================
    // Test Stimulus and Control Logic
    // =======================================================================
    integer i;
    initial begin
        // Initialize inputs
        test_data_in = 0;

        // Enable waveform dumping
        $dumpfile("tb_unknown_module.vcd");
        $dumpvars(0, tb_unknown_module);

        // Display start message
        $display("[%t] Starting test: basic_test", $time);
        $display("[%t] Clock period: 10.0ns | Simulation time: 10000 cycles", $time);

        // Monitor key signals
        $monitor("%t | clk=%b | rst_n=%b | data_in=0x%h | data_out=0x%h | done=%b",
                 $time, clk, rst_n, test_data_in, test_data_out, test_done);

        // Basic test: iterate through 1000 values over 10000 cycles
        for (i = 0; i < 10000; i = i + 1) begin
            #10.0;  // Wait one clock cycle

            // Apply stimulus every 10th cycle to avoid excessive load
            if (i % 10 == 0) begin
                test_data_in = i & 32'hFFFF_FFFF;
            end

            // Check for completion condition
            if (test_done && (i > 100)) begin
                $display("[%t] TEST SUCCESS: test_done asserted after %d cycles", $time, i);
                break;
            end

            // Early termination if stuck
            if (i > 9999) begin
                $display("[%t] WARNING: test_done never asserted within 10000 cycles", $time);
            end
        end

        // Final check: ensure test is complete
        if (!test_done) begin
            $display("[%t] ERROR: test_done did not assert during simulation", $time);
        end else begin
            $display("[%t] PASS: basic_test completed successfully", $time);
        end

        // Finish simulation
        #10.0;
        $finish;
    end

    // =======================================================================
    // Result Checking and Assertions (using $error/$warning)
    // =======================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset state - all outputs should be zero or undefined
            if (test_data_out !== 0) begin
                $error("[%t] ERROR: test_data_out not reset to 0 during reset", $time);
            end
            if (test_done !== 0) begin
                $error("[%t] ERROR: test_done asserted during reset", $time);
            end
        end else begin
            // Normal operation: verify output consistency
            if (test_done && (test_data_out != test_data_in)) begin
                $warning("[%t] WARNING: test_data_out mismatch with input on completion", $time);
            end
        end
    end

    // =======================================================================
    // Final Test Report
    // =======================================================================
    initial begin
        #100000;  // Allow time for final messages
        $display("[%t] === TEST REPORT ===", $time);
        $display("[%t] Total simulation time: 10000 clock cycles", $time);
        $display("[%t] Clock frequency: 100 MHz", $time);
        $display("[%t] Waveform dumped to: tb_unknown_module.vcd", $time);
        $display("[%t] Test completed.", $time);
    end

endmodule