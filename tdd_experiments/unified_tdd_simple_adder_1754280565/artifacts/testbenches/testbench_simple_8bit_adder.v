`timescale 1ns/1ps

module tb_simple_8bit_adder;

    // Testbench signals
    reg  [7:0] a;
    reg  [7:0] b;
    reg        cin;
    wire [7:0] sum;
    wire       cout;
    
    // Clock and control signals
    reg        clk;
    reg        rst_n;
    
    // Test status signals
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
    
    // Generate clock with 10.0ns period
    always begin
        #5 clk = ~clk;
    end
    
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
        
        // Start waveform dumping
        $dumpfile("simple_8bit_adder.vcd");
        $dumpvars(0, tb_simple_8bit_adder);
        
        // Apply reset
        #10 rst_n = 1'b1;
        
        // Run tests
        basic_functionality();
        carry_propagation();
        boundary_conditions();
        
        // Finish simulation
        #100;
        $display("Testbench completed at time %0t", $time);
        $display("Total errors detected: %0d", error_count);
        
        if (error_count == 0) begin
            $display("PASS: All tests passed successfully!");
        end else begin
            $display("FAIL: %0d test(s) failed!", error_count);
        end
        
        $finish;
    end
    
    // Monitor signals for debugging
    initial begin
        $monitor("Time=%0t: a=%b b=%b cin=%b sum=%b cout=%b", 
                 $time, a, b, cin, sum, cout);
    end
    
    // Basic functionality test
    task basic_functionality;
        integer j;
        begin
            $display("Starting basic_functionality test at time %0t", $time);
            
            // Test cases for basic addition without carry
            for (j = 0; j < 100; j = j + 1) begin
                a = $random % 256;
                b = $random % 256;
                cin = 1'b0;
                
                #10;
                
                // Check results
                if ((a + b) != sum) begin
                    $display("ERROR: Basic test failed at time %0t - Expected sum=%b, Got sum=%b", 
                             $time, (a + b), sum);
                    error_count = error_count + 1;
                end
                
                if (((a + b) > 255) != cout) begin
                    $display("ERROR: Basic test carry failed at time %0t - Expected cout=%b, Got cout=%b", 
                             $time, ((a + b) > 255), cout);
                    error_count = error_count + 1;
                end
            end
            
            $display("Completed basic_functionality test at time %0t", $time);
        end
    endtask
    
    // Carry propagation test
    task carry_propagation;
        integer k;
        begin
            $display("Starting carry_propagation test at time %0t", $time);
            
            // Test cases with carry propagation
            for (k = 0; k < 50; k = k + 1) begin
                a = 8'hFF;  // Maximum value
                b = 8'h01;  // Small value
                cin = 1'b0;
                
                #10;
                
                // Check that carry is generated
                if (cout != 1'b1) begin
                    $display("ERROR: Carry propagation test failed at time %0t - Expected cout=1'b1, Got cout=%b", 
                             $time, cout);
                    error_count = error_count + 1;
                end
                
                if (sum != 8'h00) begin
                    $display("ERROR: Carry propagation sum test failed at time %0t - Expected sum=8'h00, Got sum=%b", 
                             $time, sum);
                    error_count = error_count + 1;
                end
                
                // Test with carry in
                a = 8'hFE;
                b = 8'h01;
                cin = 1'b1;
                
                #10;
                
                if (cout != 1'b1) begin
                    $display("ERROR: Carry in test failed at time %0t - Expected cout=1'b1, Got cout=%b", 
                             $time, cout);
                    error_count = error_count + 1;
                end
                
                if (sum != 8'h00) begin
                    $display("ERROR: Carry in sum test failed at time %0t - Expected sum=8'h00, Got sum=%b", 
                             $time, sum);
                    error_count = error_count + 1;
                end
            end
            
            $display("Completed carry_propagation test at time %0t", $time);
        end
    endtask
    
    // Boundary conditions test
    task boundary_conditions;
        integer l;
        begin
            $display("Starting boundary_conditions test at time %0t", $time);
            
            // Test zero inputs
            for (l = 0; l < 10; l = l + 1) begin
                a = 8'b0;
                b = 8'b0;
                cin = 1'b0;
                
                #10;
                
                if (sum != 8'b0) begin
                    $display("ERROR: Zero input test failed at time %0t - Expected sum=8'b0, Got sum=%b", 
                             $time, sum);
                    error_count = error_count + 1;
                end
                
                if (cout != 1'b0) begin
                    $display("ERROR: Zero input carry test failed at time %0t - Expected cout=1'b0, Got cout=%b", 
                             $time, cout);
                    error_count = error_count + 1;
                end
            end
            
            // Test maximum values
            a = 8'hFF;
            b = 8'hFF;
            cin = 1'b1;
            
            #10;
            
            if (sum != 8'hFE) begin
                $display("ERROR: Maximum values test failed at time %0t - Expected sum=8'hFE, Got sum=%b", 
                         $time, sum);
                error_count = error_count + 1;
            end
            
            if (cout != 1'b1) begin
                $display("ERROR: Maximum values carry test failed at time %0t - Expected cout=1'b1, Got cout=%b", 
                         $time, cout);
                error_count = error_count + 1;
            end
            
            // Test with carry in
            a = 8'hFF;
            b = 8'h00;
            cin = 1'b1;
            
            #10;
            
            if (sum != 8'h00) begin
                $display("ERROR: Carry in test failed at time %0t - Expected sum=8'h00, Got sum=%b", 
                         $time, sum);
                error_count = error_count + 1;
            end
            
            if (cout != 1'b1) begin
                $display("ERROR: Carry in carry test failed at time %0t - Expected cout=1'b1, Got cout=%b", 
                         $time, cout);
                error_count = error_count + 1;
            end
            
            $display("Completed boundary_conditions test at time %0t", $time);
        end
    endtask

endmodule