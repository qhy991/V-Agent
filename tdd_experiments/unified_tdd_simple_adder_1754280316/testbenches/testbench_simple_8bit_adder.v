`timescale 1ns/1ps

module tb_simple_8bit_adder;

    // Testbench signals
    reg  [7:0] a;
    reg  [7:0] b;
    reg        cin;
    wire [7:0] sum;
    wire       cout;
    
    // Clock and reset signals
    reg        clk;
    reg        rst_n;
    
    // Test control signals
    integer    i;
    integer    test_case;
    integer    error_count;
    
    // Instantiate the Unit Under Test (UUT)
    simple_8bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );
    
    // Generate clock signal
    always #5.0 clk = ~clk;
    
    // Initialize simulation
    initial begin
        // Initialize all signals
        a = 8'b0;
        b = 8'b0;
        cin = 1'b0;
        clk = 1'b0;
        rst_n = 1'b0;
        
        // Initialize error counter
        error_count = 0;
        
        // Display start message
        $display("Starting testbench for simple_8bit_adder at time %0t", $time);
        $dumpfile("simple_8bit_adder.vcd");
        $dumpvars(0, tb_simple_8bit_adder);
        
        // Apply reset
        #10;
        rst_n = 1'b1;
        
        // Run basic functionality test
        $display("Running basic functionality test...");
        test_basic_functionality();
        
        // Run boundary conditions test
        $display("Running boundary conditions test...");
        test_boundary_conditions();
        
        // Run carry propagation test
        $display("Running carry propagation test...");
        test_carry_propagation();
        
        // Display final results
        $display("Test completed at time %0t", $time);
        $display("Total errors detected: %0d", error_count);
        
        if (error_count == 0) begin
            $display("PASS: All tests passed successfully!");
        end else begin
            $display("FAIL: %0d errors detected in testing", error_count);
        end
        
        $finish;
    end
    
    // Monitor signals for debugging
    initial begin
        $monitor("Time=%0t: a=%b b=%b cin=%b sum=%b cout=%b", 
                 $time, a, b, cin, sum, cout);
    end
    
    // Basic functionality test
    task test_basic_functionality;
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
                        $display("ERROR: Carry out mismatch at time %0t", $time);
                        error_count = error_count + 1;
                    end
                end else begin
                    if (cout != 1'b0) begin
                        $display("ERROR: Carry out mismatch at time %0t", $time);
                        error_count = error_count + 1;
                    end
                end
                
                if (sum != (a + b + cin)) begin
                    $display("ERROR: Sum mismatch at time %0t", $time);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Boundary conditions test
    task test_boundary_conditions;
        integer k;
        begin
            // Test zero inputs
            a = 8'b0;
            b = 8'b0;
            cin = 1'b0;
            #10;
            if ((sum != 8'b0) || (cout != 1'b0)) begin
                $display("ERROR: Zero inputs test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Test maximum values
            a = 8'b11111111;
            b = 8'b00000000;
            cin = 1'b1;
            #10;
            if ((sum != 8'b00000000) || (cout != 1'b1)) begin
                $display("ERROR: Maximum value test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Test all ones
            a = 8'b11111111;
            b = 8'b11111111;
            cin = 1'b1;
            #10;
            if ((sum != 8'b11111111) || (cout != 1'b1)) begin
                $display("ERROR: All ones test failed at time %0t", $time);
                error_count = error_count + 1;
            end
            
            // Test specific boundary cases
            for (k = 0; k < 10; k = k + 1) begin
                a = 8'hFF;
                b = 8'h01;
                cin = 1'b0;
                #10;
                if ((sum != 8'h00) || (cout != 1'b1)) begin
                    $display("ERROR: Boundary case 1 failed at time %0t", $time);
                    error_count = error_count + 1;
                end
                
                a = 8'h7F;
                b = 8'h01;
                cin = 1'b0;
                #10;
                if ((sum != 8'h80) || (cout != 1'b0)) begin
                    $display("ERROR: Boundary case 2 failed at time %0t", $time);
                    error_count = error_count + 1;
                end
                
                a = 8'hFF;
                b = 8'hFF;
                cin = 1'b0;
                #10;
                if ((sum != 8'hFE) || (cout != 1'b1)) begin
                    $display("ERROR: Boundary case 3 failed at time %0t", $time);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Carry propagation test
    task test_carry_propagation;
        integer l;
        begin
            // Test sequential carry propagation
            for (l = 0; l < 50; l = l + 1) begin
                a = 8'b11111111;
                b = 8'b00000001;
                cin = 1'b0;
                #10;
                
                if ((sum != 8'b00000000) || (cout != 1'b1)) begin
                    $display("ERROR: Carry propagation test failed at time %0t", $time);
                    error_count = error_count + 1;
                end
                
                a = 8'b11111110;
                b = 8'b00000001;
                cin = 1'b1;
                #10;
                
                if ((sum != 8'b00000000) || (cout != 1'b1)) begin
                    $display("ERROR: Carry propagation test failed at time %0t", $time);
                    error_count = error_count + 1;
                end
                
                a = 8'b10000000;
                b = 8'b10000000;
                cin = 1'b0;
                #10;
                
                if ((sum != 8'b00000000) || (cout != 1'b1)) begin
                    $display("ERROR: Carry propagation test failed at time %0t", $time);
                    error_count = error_count + 1;
                end
            end
        end
    endtask

endmodule