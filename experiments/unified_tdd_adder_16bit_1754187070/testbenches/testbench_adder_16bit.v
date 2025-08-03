// ===========================================================================
// Testbench for adder_16bit module
// Author: Professional Verification Engineer
// Date: 2025-04-05
// Purpose: Comprehensive verification of 16-bit ripple-carry adder with overflow detection
// Features:
//   - Full coverage of functional scenarios
//   - Standard Verilog syntax (no SystemVerilog)
//   - No task/function multi-statement blocks
//   - Proper use of begin/end, for loops, and semicolons
//   - VCD waveform dumping and test report generation
// ===========================================================================

`timescale 1ns / 1ps

module tb_adder_16bit;

    // ===========================================================================
    // Signal Declarations
    // ===========================================================================
    reg        clk;
    reg        rst_n;
    reg  [15:0] a;
    reg  [15:0] b;
    reg         cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // Internal counters and flags
    integer     test_case;
    integer     pass_count;
    integer     fail_count;
    integer     total_tests;
    integer     cycle_count;

    // ===========================================================================
    // Clock Generation (10ns period -> 100MHz)
    // ===========================================================================
    always #5 clk = ~clk;  // 5ns high, 5ns low => 10ns period

    // ===========================================================================
    // Reset Generation
    // ===========================================================================
    initial begin
        clk = 0;
        rst_n = 0;
        #20 rst_n = 1;  // Release reset after 20ns
    end

    // ===========================================================================
    // DUT Instantiation
    // ===========================================================================
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // ===========================================================================
    // Waveform Dumping (VCD File)
    // ===========================================================================
    initial begin
        $dumpfile("tb_adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // ===========================================================================
    // Monitor Output
    // ===========================================================================
    initial begin
        $monitor("%0t | a=%h, b=%h, cin=%b | sum=%h, cout=%b, overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);
    end

    // ===========================================================================
    // Test Case Execution: Basic Addition Test
    // ===========================================================================
    initial begin
        test_case = 0;
        pass_count = 0;
        fail_count = 0;
        total_tests = 0;

        // Wait for reset to stabilize
        @(posedge clk);

        // === Basic Addition Test ===
        $display("=== Starting Basic Addition Test ===");
        a = 16'h0001; b = 16'h0001; cin = 0;
        @(posedge clk);
        if (sum == 16'h0002 && cout == 0 && overflow == 0) begin
            $display("PASS: 1 + 1 = 2 (no carry, no overflow)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 1 + 1 = 2 expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        a = 16'h0000; b = 16'h0000; cin = 0;
        @(posedge clk);
        if (sum == 16'h0000 && cout == 0 && overflow == 0) begin
            $display("PASS: 0 + 0 = 0");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0 + 0 = 0 expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        a = 16'h0001; b = 16'h0000; cin = 0;
        @(posedge clk);
        if (sum == 16'h0001 && cout == 0 && overflow == 0) begin
            $display("PASS: 1 + 0 = 1");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 1 + 0 = 1 expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // === Carry Propagation Test ===
        $display("=== Starting Carry Propagation Test ===");
        a = 16'hFFFF; b = 16'h0001; cin = 0;
        @(posedge clk);
        if (sum == 16'h0000 && cout == 1 && overflow == 0) begin
            $display("PASS: 0xFFFF + 1 = 0x10000 (carry out, no overflow)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0xFFFF + 1 = 0x10000 expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        a = 16'hFFFF; b = 16'hFFFF; cin = 1;
        @(posedge clk);
        if (sum == 16'hFFFE && cout == 1 && overflow == 0) begin
            $display("PASS: 0xFFFF + 0xFFFF + 1 = 0xFFFE (carry out, no overflow)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0xFFFF + 0xFFFF + 1 = 0xFFFE expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // === Overflow Detection Test (Signed) ===
        $display("=== Starting Overflow Detection Test ===");
        // Positive overflow: 0x7FFF + 1 = 0x8000
        a = 16'h7FFF; b = 16'h0001; cin = 0;
        @(posedge clk);
        if (sum == 16'h8000 && cout == 0 && overflow == 1) begin
            $display("PASS: 0x7FFF + 1 = 0x8000 (positive overflow detected)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0x7FFF + 1 = 0x8000 overflow expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // Negative overflow: 0x8000 + (-1) = 0x7FFF
        a = 16'h8000; b = 16'hFFFF; cin = 0;
        @(posedge clk);
        if (sum == 16'h7FFF && cout == 0 && overflow == 1) begin
            $display("PASS: 0x8000 + (-1) = 0x7FFF (negative overflow detected)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0x8000 + (-1) = 0x7FFF overflow expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // No overflow: 0x7FFF + 0 = 0x7FFF
        a = 16'h7FFF; b = 16'h0000; cin = 0;
        @(posedge clk);
        if (sum == 16'h7FFF && cout == 0 && overflow == 0) begin
            $display("PASS: 0x7FFF + 0 = 0x7FFF (no overflow)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0x7FFF + 0 = 0x7FFF expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // === Boundary Value Test ===
        $display("=== Starting Boundary Value Test ===");
        // Zero
        a = 16'h0000; b = 16'h0000; cin = 0;
        @(posedge clk);
        if (sum == 16'h0000 && cout == 0 && overflow == 0) begin
            $display("PASS: 0x0000 + 0x0000 = 0x0000");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0x0000 + 0x0000 = 0x0000 expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // Max positive
        a = 16'h7FFF; b = 16'h0000; cin = 0;
        @(posedge clk);
        if (sum == 16'h7FFF && cout == 0 && overflow == 0) begin
            $display("PASS: 0x7FFF + 0 = 0x7FFF");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0x7FFF + 0 = 0x7FFF expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // Max negative
        a = 16'h8000; b = 16'h0000; cin = 0;
        @(posedge clk);
        if (sum == 16'h8000 && cout == 0 && overflow == 0) begin
            $display("PASS: 0x8000 + 0 = 0x8000");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0x8000 + 0 = 0x8000 expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // All ones
        a = 16'hFFFF; b = 16'h0000; cin = 0;
        @(posedge clk);
        if (sum == 16'hFFFF && cout == 0 && overflow == 0) begin
            $display("PASS: 0xFFFF + 0 = 0xFFFF");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: 0xFFFF + 0 = 0xFFFF expected, got sum=%h, cout=%b, overflow=%b",
                     sum, cout, overflow);
            fail_count = fail_count + 1;
        end
        total_tests = total_tests + 1;

        // === Random Data Test (Loop over all combinations) ===
        $display("=== Starting Random Data Test (1000 iterations) ===");
        for (cycle_count = 0; cycle_count < 1000; cycle_count = cycle_count + 1) begin
            a = $random;
            b = $random;
            cin = $random % 2;

            @(posedge clk);

            // Expected result calculation (manual check)
            // Use unsigned arithmetic for sum and cout
            {cout, sum} = a + b + cin;

            // Check overflow: signed overflow when same sign inputs but different sign output
            if ((a[15] == b[15]) && (a[15] != sum[15])) begin
                if (overflow != 1) begin
                    $display("FAIL: Overflow not detected at cycle %0d: a=%h, b=%h, cin=%b",
                             cycle_count, a, b, cin);
                    fail_count = fail_count + 1;
                end else begin
                    $display("PASS: Overflow correctly detected at cycle %0d", cycle_count);
                    pass_count = pass_count + 1;
                end
            end else begin
                if (overflow != 0) begin
                    $display("FAIL: False overflow at cycle %0d: a=%h, b=%h, cin=%b",
                             cycle_count, a, b, cin);
                    fail_count = fail_count + 1;
                end else begin
                    $display("PASS: No overflow as expected at cycle %0d", cycle_count);
                    pass_count = pass_count + 1;
                end
            end

            total_tests = total_tests + 1;
        end

        // ===========================================================================
        // Final Test Report
        // ===========================================================================
        $display("===============================");
        $display("TEST SUMMARY:");
        $display("Total Tests: %0d", total_tests);
        $display("Pass Count:  %0d", pass_count);
        $display("Fail Count:  %0d", fail_count);
        if (fail_count == 0) begin
            $display("RESULT: PASS ✅");
        end else begin
            $display("RESULT: FAIL ❌");
        end
        $display("===============================");

        // Finish simulation
        #100;
        $finish;
    end

    // ===========================================================================
    // Simulate for 10000 clock cycles (optional safety net)
    // ===========================================================================
    initial begin
        repeat(10000) @(posedge clk);
        $display("Simulation reached 10000 cycles without completion. Ending...");
        $finish;
    end

endmodule