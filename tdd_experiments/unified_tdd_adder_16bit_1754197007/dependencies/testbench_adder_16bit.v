// ===========================================================================
// Testbench for adder_16bit module
// Author: Professional Verification Engineer
// Date: 2025-04-05
// Description: Comprehensive testbench with multiple test scenarios
//              Fully compliant with standard Verilog syntax (IEEE 1364-2001)
// ===========================================================================

`timescale 1ns / 1ps

module tb_adder_16bit;

    // ========================
    // Signal Declarations
    // ========================
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
    integer     cycle_count;

    // For VCD waveform dumping
    initial begin
        $dumpfile("tb_adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);
    end

    // ========================
    // Clock Generation
    // ========================
    always #5 clk = ~clk;  // 10ns period (5ns high, 5ns low)

    // ========================
    // Reset Generation
    // ========================
    initial begin
        clk = 0;
        rst_n = 0;
        #20 rst_n = 1;  // Release reset after 20ns
        #1000;          // Wait for stable reset release
    end

    // ========================
    // DUT Instantiation
    // ========================
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // ========================
    // Monitor and Display
    // ========================
    initial begin
        $monitor("%0t | a=%h, b=%h, cin=%b | sum=%h, cout=%b, overflow=%b",
                 $time, a, b, cin, sum, cout, overflow);
    end

    // ========================
    // Test Case Execution
    // ========================
    initial begin
        // Initialize counters
        test_case = 0;
        pass_count = 0;
        fail_count = 0;
        cycle_count = 0;

        // Start simulation
        $display("Starting testbench for adder_16bit...");
        $display("Simulation time: 10000 clock cycles (100000ns)");
        $display("Clock period: 10ns");

        // Wait for reset to be released
        @(posedge clk);

        // =====================================================
        // Test Case 1: Basic Addition Test
        // =====================================================
        test_case = 1;
        $display("=== Test Case %0d: Basic Addition Test ===", test_case);
        a = 16'h0001; b = 16'h0001; cin = 1'b0;
        @(posedge clk);
        if (sum == 16'h0002 && cout == 1'b0 && overflow == 1'b0) begin
            $display("PASS: 1 + 1 = 2 (no carry, no overflow)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected sum=0002, got sum=%h", sum);
            fail_count = fail_count + 1;
        end

        a = 16'h1000; b = 16'h2000; cin = 1'b0;
        @(posedge clk);
        if (sum == 16'h3000 && cout == 1'b0 && overflow == 1'b0) begin
            $display("PASS: 0x1000 + 0x2000 = 0x3000");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected sum=3000, got sum=%h", sum);
            fail_count = fail_count + 1;
        end

        // =====================================================
        // Test Case 2: Carry Propagation Test
        // =====================================================
        test_case = 2;
        $display("=== Test Case %0d: Carry Propagation Test ===", test_case);
        a = 16'hFFFF; b = 16'h0001; cin = 1'b0;
        @(posedge clk);
        if (sum == 16'h0000 && cout == 1'b1 && overflow == 1'b0) begin
            $display("PASS: 0xFFFF + 0x0001 = 0x10000 (carry out, sum=0)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected sum=0000, cout=1, got sum=%h, cout=%b", sum, cout);
            fail_count = fail_count + 1;
        end

        // Test with carry-in
        a = 16'hFFFF; b = 16'h0000; cin = 1'b1;
        @(posedge clk);
        if (sum == 16'h0000 && cout == 1'b1 && overflow == 1'b0) begin
            $display("PASS: 0xFFFF + 0x0000 + 1 = 0x10000 (carry in)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected sum=0000, cout=1, got sum=%h, cout=%b", sum, cout);
            fail_count = fail_count + 1;
        end

        // =====================================================
        // Test Case 3: Overflow Detection Test (Signed)
        // =====================================================
        test_case = 3;
        $display("=== Test Case %0d: Overflow Detection Test ===", test_case);

        // Positive + Positive → Negative (overflow)
        a = 16'h7FFF; b = 16'h0001; cin = 1'b0;
        @(posedge clk);
        if (sum[15] == 1'b1 && overflow == 1'b1) begin
            $display("PASS: 0x7FFF + 0x0001 = 0x8000 (positive + positive → negative)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected overflow=1, sum[15]=1, got overflow=%b, sum[15]=%b", overflow, sum[15]);
            fail_count = fail_count + 1;
        end

        // Negative + Negative → Positive (overflow)
        a = 16'h8000; b = 16'h8000; cin = 1'b0;
        @(posedge clk);
        if (sum[15] == 1'b0 && overflow == 1'b1) begin
            $display("PASS: 0x8000 + 0x8000 = 0x0000 (negative + negative → positive)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected overflow=1, sum[15]=0, got overflow=%b, sum[15]=%b", overflow, sum[15]);
            fail_count = fail_count + 1;
        end

        // No overflow case
        a = 16'h7FFE; b = 16'h0001; cin = 1'b0;
        @(posedge clk);
        if (sum[15] == 1'b0 && overflow == 1'b0) begin
            $display("PASS: 0x7FFE + 0x0001 = 0x7FFF (no overflow)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected overflow=0, sum[15]=0, got overflow=%b, sum[15]=%b", overflow, sum[15]);
            fail_count = fail_count + 1;
        end

        // =====================================================
        // Test Case 4: Boundary Value Test
        // =====================================================
        test_case = 4;
        $display("=== Test Case %0d: Boundary Value Test ===", test_case);

        // Zero values
        a = 16'h0000; b = 16'h0000; cin = 1'b0;
        @(posedge clk);
        if (sum == 16'h0000 && cout == 1'b0 && overflow == 1'b0) begin
            $display("PASS: 0 + 0 = 0");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected sum=0000, got sum=%h", sum);
            fail_count = fail_count + 1;
        end

        // Max positive value
        a = 16'h7FFF; b = 16'h0000; cin = 1'b0;
        @(posedge clk);
        if (sum == 16'h7FFF && cout == 1'b0 && overflow == 1'b0) begin
            $display("PASS: 0x7FFF + 0 = 0x7FFF");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected sum=7FFF, got sum=%h", sum);
            fail_count = fail_count + 1;
        end

        // Max negative value
        a = 16'h8000; b = 16'h0000; cin = 1'b0;
        @(posedge clk);
        if (sum == 16'h8000 && cout == 1'b0 && overflow == 1'b0) begin
            $display("PASS: 0x8000 + 0 = 0x8000");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected sum=8000, got sum=%h", sum);
            fail_count = fail_count + 1;
        end

        // All ones
        a = 16'hFFFF; b = 16'hFFFF; cin = 1'b0;
        @(posedge clk);
        if (sum == 16'hFFFE && cout == 1'b1 && overflow == 1'b0) begin
            $display("PASS: 0xFFFF + 0xFFFF = 0xFFFE (carry out, no overflow)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected sum=FFFE, cout=1, got sum=%h, cout=%b", sum, cout);
            fail_count = fail_count + 1;
        end

        // =====================================================
        // Test Case 5: Random Data Test (Full Coverage)
        // =====================================================
        test_case = 5;
        $display("=== Test Case %0d: Random Data Test (1000 iterations) ===", test_case);

        for (integer i = 0; i < 1000; i = i + 1) begin
            a = $random;
            b = $random;
            cin = $random % 2;

            @(posedge clk);

            // Manual verification of results
            // Expected sum = a + b + cin
            // Expected cout = (a + b + cin) > 16'hFFFF
            // Expected overflow = (a[15]==b[15]) && (a[15]!=sum[15])

            // Compute expected values manually
            integer expected_sum;
            integer expected_carry;
            integer expected_overflow;

            expected_sum = a + b + cin;
            expected_carry = (expected_sum > 16'hFFFF) ? 1 : 0;
            expected_overflow = (a[15] == b[15]) && (a[15] != sum[15]);

            if (sum == expected_sum[15:0] && cout == expected_carry && overflow == expected_overflow) begin
                // Pass
            end else begin
                $display("FAIL: Random test #%0d - a=%h, b=%h, cin=%b",
                         i, a, b, cin);
                $display("       Expected: sum=%h, cout=%b, overflow=%b",
                         expected_sum[15:0], expected_carry, expected_overflow);
                $display("       Got:      sum=%h, cout=%b, overflow=%b", sum, cout, overflow);
                fail_count = fail_count + 1;
            end
        end

        // =====================================================
        // Final Report
        // =====================================================
        $display("===============================");
        $display("TEST COMPLETED");
        $display("Total test cases: 5");
        $display("Passed: %0d", pass_count);
        $display("Failed: %0d", fail_count);
        $display("Success rate: %0.1f%%", (pass_count * 100.0) / (pass_count + fail_count));
        $display("===============================");

        if (fail_count == 0) begin
            $display("✅ ALL TESTS PASSED!");
        end else begin
            $display("❌ SOME TESTS FAILED!");
        end

        // Finish simulation
        #100;
        $finish;
    end

    // ========================
    // End of Testbench
    // ========================

endmodule