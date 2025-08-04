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
        error_count = 0;
        
        // Start waveform dumping
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
        
        // Run basic functionality tests
        test_case = 1;
        $display("Running basic functionality test...");
        basic_functionality_test();
        
        // Run carry propagation tests
        test_case = 2;
        $display("Running carry propagation test...");
        carry_propagation_test();
        
        // Run boundary condition tests
        test_case = 3;
        $display("Running boundary conditions test...");
        boundary_conditions_test();
        
        // Display final results
        $display("===============================================");
        if (error_count == 0) begin
            $display("TEST RESULT: PASSED - All tests completed successfully");
        end else begin
            $display("TEST RESULT: FAILED - %d errors detected", error_count);
        end
        $display("===============================================");
        
        // Finish simulation
        #100;
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
            for (j=0; j<256; j=j+1) begin
                a = j;
                b = 8'h00;
                cin = 1'b0;
                #10;
                if (sum !== a) begin
                    $display("ERROR: Basic test failed at a=%b, expected sum=%b, got sum=%b", 
                             a, a, sum);
                    error_count = error_count + 1;
                end
            end
            
            for (j=0; j<256; j=j+1) begin
                a = 8'h00;
                b = j;
                cin = 1'b0;
                #10;
                if (sum !== b) begin
                    $display("ERROR: Basic test failed at b=%b, expected sum=%b, got sum=%b", 
                             b, b, sum);
                    error_count = error_count + 1;
                end
            end
            
            for (j=0; j<256; j=j+1) begin
                a = j;
                b = j;
                cin = 1'b0;
                #10;
                if (sum !== (a+b)) begin
                    $display("ERROR: Basic test failed at a=%b, b=%b, expected sum=%b, got sum=%b", 
                             a, b, (a+b), sum);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Carry propagation test
    task carry_propagation_test;
        integer j;
        begin
            // Test cases with carry propagation
            a = 8'hFF;
            b = 8'h01;
            cin = 1'b0;
            #10;
            if ((sum !== 8'h00) || (cout !== 1'b1)) begin
                $display("ERROR: Carry propagation test failed - a=%b, b=%b, cin=%b, sum=%b, cout=%b", 
                         a, b, cin, sum, cout);
                error_count = error_count + 1;
            end
            
            a = 8'h7F;
            b = 8'h01;
            cin = 1'b0;
            #10;
            if ((sum !== 8'h80) || (cout !== 1'b0)) begin
                $display("ERROR: Carry propagation test failed - a=%b, b=%b, cin=%b, sum=%b, cout=%b", 
                         a, b, cin, sum, cout);
                error_count = error_count + 1;
            end
            
            a = 8'hFF;
            b = 8'hFF;
            cin = 1'b1;
            #10;
            if ((sum !== 8'hFE) || (cout !== 1'b1)) begin
                $display("ERROR: Carry propagation test failed - a=%b, b=%b, cin=%b, sum=%b, cout=%b", 
                         a, b, cin, sum, cout);
                error_count = error_count + 1;
            end
            
            // Test multiple carries
            a = 8'h7F;
            b = 8'h7F;
            cin = 1'b1;
            #10;
            if ((sum !== 8'hFE) || (cout !== 1'b1)) begin
                $display("ERROR: Carry propagation test failed - a=%b, b=%b, cin=%b, sum=%b, cout=%b", 
                         a, b, cin, sum, cout);
                error_count = error_count + 1;
            end
        end
    endtask
    
    // Boundary conditions test
    task boundary_conditions_test;
        integer j;
        begin
            // Test zero inputs
            a = 8'h00;
            b = 8'h00;
            cin = 1'b0;
            #10;
            if ((sum !== 8'h00) || (cout !== 1'b0)) begin
                $display("ERROR: Boundary test failed - Zero inputs - a=%b, b=%b, cin=%b, sum=%b, cout=%b", 
                         a, b, cin, sum, cout);
                error_count = error_count + 1;
            end
            
            // Test maximum values
            a = 8'hFF;
            b = 8'hFF;
            cin = 1'b1;
            #10;
            if ((sum !== 8'hFE) || (cout !== 1'b1)) begin
                $display("ERROR: Boundary test failed - Max values - a=%b, b=%b, cin=%b, sum=%b, cout=%b", 
                         a, b, cin, sum, cout);
                error_count = error_count + 1;
            end
            
            // Test with carry in
            a = 8'h00;
            b = 8'h00;
            cin = 1'b1;
            #10;
            if ((sum !== 8'h01) || (cout !== 1'b0)) begin
                $display("ERROR: Boundary test failed - Carry in - a=%b, b=%b, cin=%b, sum=%b, cout=%b", 
                         a, b, cin, sum, cout);
                error_count = error_count + 1;
            end
            
            // Test with carry out
            a = 8'hFF;
            b = 8'h01;
            cin = 1'b0;
            #10;
            if ((sum !== 8'h00) || (cout !== 1'b1)) begin
                $display("ERROR: Boundary test failed - Carry out - a=%b, b=%b, cin=%b, sum=%b, cout=%b", 
                         a, b, cin, sum, cout);
                error_count = error_count + 1;
            end
            
            // Test specific boundary cases
            for (j=0; j<8; j=j+1) begin
                a = 8'h00;
                b = 8'h01 << j;
                cin = 1'b0;
                #10;
                if (sum !== (8'h01 << j)) begin
                    $display("ERROR: Boundary test failed - Specific case - a=%b, b=%b, cin=%b, sum=%b", 
                             a, b, cin, sum);
                    error_count = error_count + 1;
                end
            end
        end
    endtask

endmodule