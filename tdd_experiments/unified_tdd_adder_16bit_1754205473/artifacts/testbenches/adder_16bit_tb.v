`timescale 1ns / 1ps

module tb_adder_16bit;

    reg [15:0] a, b;
    reg        cin;
    wire [15:0] sum;
    wire        cout;
    wire        overflow;

    // Clock generation
    parameter CLK_PERIOD = 10;
    reg clk;
    always # (CLK_PERIOD/2) clk = ~clk;

    // Testbench variables
    integer test_case;
    integer cycle_count;

    // Instantiate DUT
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    initial begin
        // Initialize signals
        a = 16'd0;
        b = 16'd0;
        cin = 1'b0;
        test_case = 1;
        cycle_count = 0;

        // Enable waveform dumping
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Display header
        $display("Starting simulation for adder_16bit module");
        $display("%t | Test Case | A       | B       | Cin | Sum     | Cout | Overflow", $time);

        // Test case 1: Add two positive numbers within range
        #10;
        a = 16'd100;
        b = 16'd200;
        cin = 1'b0;
        #10;
        $display("%t | %d         | %d      | %d     | %d   | %d      | %d   | %d", $time, test_case++, a, b, cin, sum, cout, overflow);

        // Test case 2: Add two negative numbers (check overflow)
        #10;
        a = 16'd'haaaa;  // -17446 in signed 16-bit
        b = 16'd'haaaa;
        cin = 1'b0;
        #10;
        $display("%t | %d         | %d      | %d     | %d   | %d      | %d   | %d", $time, test_case++, a, b, cin, sum, cout, overflow);

        // Test case 3: Add max positive and min negative
        #10;
        a = 16'd32767;   // Max positive
        b = 16'd-32768;  // Min negative
        cin = 1'b0;
        #10;
        $display("%t | %d         | %d      | %d     | %d   | %d      | %d   | %d", $time, test_case++, a, b, cin, sum, cout, overflow);

        // Test case 4: Edge case with cin=1 and all bits high
        #10;
        a = 16'd'ffff;
        b = 16'd'ffff;
        cin = 1'b1;
        #10;
        $display("%t | %d         | %d      | %d     | %d   | %d      | %d   | %d", $time, test_case++, a, b, cin, sum, cout, overflow);

        // Test case 5: Zero inputs with cin=1
        #10;
        a = 16'd0;
        b = 16'd0;
        cin = 1'b1;
        #10;
        $display("%t | %d         | %d      | %d     | %d   | %d      | %d   | %d", $time, test_case++, a, b, cin, sum, cout, overflow);

        // Final check
        #10;
        $display("Simulation complete. Total cycles: %0d", cycle_count);
        $finish;
    end

    // Monitor signals
    initial begin
        $monitor("%t | %d | %d | %b | %d | %b | %b", $time, a, b, cin, sum, cout, overflow);
    end

    // Clock counter
    always @(posedge clk) begin
        cycle_count <= cycle_count + 1;
        if (cycle_count >= 100) begin
            $display("Reached maximum simulation time of 1000 ns.");
            $finish;
        end
    end

endmodule