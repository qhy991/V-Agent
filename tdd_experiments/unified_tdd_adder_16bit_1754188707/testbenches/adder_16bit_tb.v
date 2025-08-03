`timescale 1ns / 1ps

module tb_adder_16bit;

    // Signal declarations
    reg [15:0] a;
    reg [15:0] b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // DUT instantiation
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    // Clock generation
    parameter CLK_PERIOD = 10ns;
    reg clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // Initial block for simulation control and test cases
    initial begin
        // Enable waveform dumping
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Initialize inputs
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;

        // Monitor signals
        $monitor("%t | a=%d, b=%d, cin=%b | sum=%d, cout=%b, overflow=%b", 
                 $time, a, b, cin, sum, cout, overflow);

        // Test case 1: Add two positive numbers (32767 + 1) → overflow
        #20 a = 16'd32767; b = 16'd1; cin = 1'b0;
        #20;
        if (sum !== 16'd0 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 1 failed. Expected sum=0, cout=1, overflow=1. Got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 1 - Positive overflow (32767 + 1)");
        end

        // Test case 2: Add two negative numbers (-32768 + -1) → overflow
        #20 a = 16'd-32768; b = 16'd-1; cin = 1'b0;
        #20;
        if (sum !== 16'd-32769 || cout !== 1'b0 || overflow !== 1'b1) begin
            $display("ERROR: Test case 2 failed. Expected sum=-32769, cout=0, overflow=1. Got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 2 - Negative overflow (-32768 + -1)");
        end

        // Test case 3: Positive + negative (1000 + (-500)) → no overflow
        #20 a = 16'd1000; b = 16'd-500; cin = 1'b0;
        #20;
        if (sum !== 16'd500 || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case 3 failed. Expected sum=500, cout=0, overflow=0. Got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 3 - Mixed signs (1000 + (-500))");
        end

        // Test case 4: Maximum value addition (0xFFFF + 0xFFFF + 1) → check cout and sum
        #20 a = 16'hFFFF; b = 16'hFFFF; cin = 1'b1;
        #20;
        if (sum !== 16'd0 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 4 failed. Expected sum=0, cout=1, overflow=1. Got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 4 - Max values with carry-in (0xFFFF + 0xFFFF + 1)");
        end

        // Test case 5: Zero inputs (0 + 0 + 0)
        #20 a = 16'd0; b = 16'd0; cin = 1'b0;
        #20;
        if (sum !== 16'd0 || cout !== 1'b0 || overflow !== 1'b0) begin
            $display("ERROR: Test case 5 failed. Expected sum=0, cout=0, overflow=0. Got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 5 - Zero inputs (0 + 0 + 0)");
        end

        // Test case 6: Boundary values: 0x7FFF + 0x7FFF → overflow expected
        #20 a = 16'h7FFF; b = 16'h7FFF; cin = 1'b0;
        #20;
        if (sum !== 16'd-2 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 6 failed. Expected sum=-2, cout=1, overflow=1. Got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 6 - Upper bound overflow (0x7FFF + 0x7FFF)");
        end

        // Test case 7: 0x8000 + 0x8000 → overflow expected (min signed + min signed)
        #20 a = 16'h8000; b = 16'h8000; cin = 1'b0;
        #20;
        if (sum !== 16'd0 || cout !== 1'b1 || overflow !== 1'b1) begin
            $display("ERROR: Test case 7 failed. Expected sum=0, cout=1, overflow=1. Got sum=%d, cout=%b, overflow=%b", sum, cout, overflow);
        end else begin
            $display("PASS: Test case 7 - Lower bound overflow (0x8000 + 0x8000)");
        end

        // Test case 8: Random input combinations
        $display("Starting random test cases...");
        repeat (100) begin
            a = $random;
            b = $random;
            cin = $random % 2;
            #20;
            // Check overflow logic manually
            logic [15:0] expected_sum;
            logic expected_cout;
            logic expected_overflow;
            {expected_cout, expected_sum} = $signed(a) + $signed(b) + cin;
            expected_overflow = (a[15] == b[15]) && (a[15] != expected_sum[15]);
            if (sum !== expected_sum || cout !== expected_cout || overflow !== expected_overflow) begin
                $display("RANDOM ERROR: a=%d, b=%d, cin=%b | Expected sum=%d, cout=%b, overflow=%b | Got sum=%d, cout=%b, overflow=%b",
                         a, b, cin, expected_sum, expected_cout, expected_overflow, sum, cout, overflow);
            end
        end
        $display("Random test cases completed.");

        // End simulation after 1000 clock cycles
        #20000;
        $display("Simulation complete.");
        $finish;
    end

endmodule