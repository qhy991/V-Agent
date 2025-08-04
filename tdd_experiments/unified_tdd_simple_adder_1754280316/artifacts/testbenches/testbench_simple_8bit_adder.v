`timescale 1ns/1ps

module tb_simple_8bit_adder;

    // Testbench signals
    reg  [7:0] a;
    reg  [7:0] b;
    reg        cin;
    wire [7:0] sum;
    wire       cout;
    
    // Clock and reset signals
    reg clk;
    reg rst_n;
    
    // Test control signals
    integer i;
    integer test_case;
    integer error_count;
    
    // Instantiate the Unit Under Test (UUT)
    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );
    
    // Generate clock
    always #5.0 clk = ~clk;
    
    // Initialize simulation
    initial begin
        // Initialize all signals
        a = 8'b0;
        b = 8'b0;
        cin = 1'b0;
        clk = 1'b0;
        rst_n = 1'b0;
        error_count = 0;
        
        // Start waveform dump
        $dumpfile("simple_8bit_adder.vcd");
        $dumpvars(0, tb_simple_8bit_adder);
        
        // Display test start message
        $display("===============================================");
        $display("Starting testbench for simple_8bit_adder module");
        $display("===============================================");
        
        // Apply reset
        #10;
        rst_n = 1'b1;
        #10;
        
        // Run basic functionality test
        test_case = 1;
        $display("Running basic_functionality test...");
        basic_functionality_test();
        
        // Run carry propagation test
        test_case = 2;
        $display("Running carry_propagation test...");
        carry_propagation_test();
        
        // Run boundary conditions test
        test_case = 3;
        $display("Running boundary_conditions test...");
        boundary_conditions_test();
        
        // Display final results
        $display("===============================================");
        $display("Testbench completed.");
        $display("Total errors detected: %d", error_count);
        $display("===============================================");
        
        if (error_count == 0) begin
            $display("PASS: All tests passed successfully!");
        end else begin
            $display("FAIL: Some tests failed with %d errors.", error_count);
        end
        
        $finish;
    end
    
    // Monitor signals for debugging
    initial begin
        $monitor("Time=%0t | a=%b b=%b cin=%b sum=%b cout=%b", 
                 $time, a, b, cin, sum, cout);
    end
    
    // Basic functionality test
    task basic_functionality_test;
        integer j;
        begin
            for (j = 0; j < 100; j = j + 1) begin
                a = $random % 256;
                b = $random % 256;
                cin = $random % 2;
                #10;
                
                // Check results
                if ((a + b + cin) > 255) begin
                    if (cout != 1'b1) begin
                        $display("ERROR: Carry out should be 1 at time %0t", $time);
                        error_count = error_count + 1;
                    end
                end else begin
                    if (cout != 1'b0) begin
                        $display("ERROR: Carry out should be 0 at time %0t", $time);
                        error_count = error_count + 1;
                    end
                end
                
                if (sum != (a + b + cin)) begin
                    $display("ERROR: Sum mismatch at time %0t. Expected: %b, Got: %b", 
                             $time, (a + b + cin), sum);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Carry propagation test
    task carry_propagation_test;
        integer k;
        begin
            // Test cases where carry propagates through all bits
            a = 8'hFF;  // 255
            b = 8'h01;  // 1
            cin = 1'b0;
            #10;
            
            if (sum != 8'h00 || cout != 1'b1) begin
                $display("ERROR: Carry propagation test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Test case with carry in
            a = 8'hFF;
            b = 8'hFF;
            cin = 1'b1;
            #10;
            
            if (sum != 8'hFE || cout != 1'b1) begin
                $display("ERROR: Carry in test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Test case with no carry
            a = 8'h7F;
            b = 8'h7F;
            cin = 1'b0;
            #10;
            
            if (sum != 8'hFE || cout != 1'b0) begin
                $display("ERROR: No carry test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Additional carry propagation tests
            for (k = 0; k < 50; k = k + 1) begin
                a = 8'hFF;
                b = 8'h01;
                cin = 1'b0;
                #10;
                
                if (sum != 8'h00 || cout != 1'b1) begin
                    $display("ERROR: Carry propagation test %d failed at time %0t", 
                             k, $time);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Boundary conditions test
    task boundary_conditions_test;
        integer l;
        begin
            // Test zero inputs
            a = 8'b0;
            b = 8'b0;
            cin = 1'b0;
            #10;
            
            if (sum != 8'b0 || cout != 1'b0) begin
                $display("ERROR: Zero inputs test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Test maximum values
            a = 8'hFF;
            b = 8'hFF;
            cin = 1'b1;
            #10;
            
            if (sum != 8'hFE || cout != 1'b1) begin
                $display("ERROR: Maximum values test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Test with carry in set to 1
            a = 8'b0;
            b = 8'b0;
            cin = 1'b1;
            #10;
            
            if (sum != 8'b1 || cout != 1'b0) begin
                $display("ERROR: Carry in test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Test specific boundary cases
            for (l = 0; l < 20; l = l + 1) begin
                a = 8'h00;
                b = 8'hFF;
                cin = 1'b1;
                #10;
                
                if (sum != 8'h00 || cout != 1'b1) begin
                    $display("ERROR: Boundary case %d failed at time %0t", 
                             l, $time);
                    error_count = error_count + 1;
                end
            end
        end
    endtask

endmodule