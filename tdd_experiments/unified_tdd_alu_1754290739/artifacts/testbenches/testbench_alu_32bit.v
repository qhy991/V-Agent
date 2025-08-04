`timescale 1ns/1ps

module tb_alu_32bit;

    // Testbench signals
    reg  [31:0] a;
    reg  [31:0] b;
    reg  [3:0]  op;
    wire [31:0] result;
    wire        zero;
    
    // Clock and reset signals
    reg clk;
    reg rst_n;
    
    // Test status signals
    integer test_index;
    integer pass_count;
    integer fail_count;
    
    // VCD file for waveform dumping
    initial begin
        $dumpfile("alu_32bit_tb.vcd");
        $dumpvars(0, tb_alu_32bit);
    end
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 10ns period clock
    end
    
    // Reset generation
    initial begin
        rst_n = 0;
        #10 rst_n = 1;
    end
    
    // Instantiate the DUT
    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );
    
    // Monitor signals
    initial begin
        $monitor("Time=%0t: a=0x%08h, b=0x%08h, op=0x%01h, result=0x%08h, zero=%b", 
                 $time, a, b, op, result, zero);
    end
    
    // Test cases
    task addition_test;
        integer i;
        begin
            $display("Starting addition_test at time %0t", $time);
            
            // Test basic addition
            a = 32'h00000001;
            b = 32'h00000002;
            op = 4'b0000;
            #10;
            
            if (result == 32'h00000003 && zero == 1'b0) begin
                $display("Addition test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("Addition test FAILED - Expected 0x00000003, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test addition with zero
            a = 32'h00000005;
            b = 32'h00000000;
            op = 4'b0000;
            #10;
            
            if (result == 32'h00000005 && zero == 1'b0) begin
                $display("Addition with zero test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("Addition with zero test FAILED - Expected 0x00000005, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test addition with overflow
            a = 32'h7FFFFFFF;
            b = 32'h00000001;
            op = 4'b0000;
            #10;
            
            if (result == 32'h80000000 && zero == 1'b0) begin
                $display("Addition overflow test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("Addition overflow test FAILED - Expected 0x80000000, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            $display("Completed addition_test at time %0t", $time);
        end
    endtask
    
    task logical_test;
        integer i;
        begin
            $display("Starting logical_test at time %0t", $time);
            
            // Test AND operation
            a = 32'hAAAAAAAA;
            b = 32'h55555555;
            op = 4'b0001;
            #10;
            
            if (result == 32'h00000000 && zero == 1'b1) begin
                $display("AND operation test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("AND operation test FAILED - Expected 0x00000000, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test OR operation
            a = 32'hAAAAAAAA;
            b = 32'h55555555;
            op = 4'b0010;
            #10;
            
            if (result == 32'hFFFFFFFF && zero == 1'b0) begin
                $display("OR operation test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("OR operation test FAILED - Expected 0xFFFFFFFF, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test XOR operation
            a = 32'hAAAAAAAA;
            b = 32'h55555555;
            op = 4'b0011;
            #10;
            
            if (result == 32'hFFFFFFFF && zero == 1'b0) begin
                $display("XOR operation test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("XOR operation test FAILED - Expected 0xFFFFFFFF, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            $display("Completed logical_test at time %0t", $time);
        end
    endtask
    
    task shift_test;
        integer i;
        begin
            $display("Starting shift_test at time %0t", $time);
            
            // Test SLL operation
            a = 32'h00000001;
            b = 32'h00000003;
            op = 4'b1000;
            #10;
            
            if (result == 32'h00000008 && zero == 1'b0) begin
                $display("SLL operation test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("SLL operation test FAILED - Expected 0x00000008, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test SRL operation
            a = 32'h00000010;
            b = 32'h00000002;
            op = 4'b1001;
            #10;
            
            if (result == 32'h00000004 && zero == 1'b0) begin
                $display("SRL operation test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("SRL operation test FAILED - Expected 0x00000004, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test SRA operation
            a = 32'h80000000;
            b = 32'h00000001;
            op = 4'b1010;
            #10;
            
            if (result == 32'hC0000000 && zero == 1'b0) begin
                $display("SRA operation test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("SRA operation test FAILED - Expected 0xC0000000, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            $display("Completed shift_test at time %0t", $time);
        end
    endtask
    
    task comparison_test;
        integer i;
        begin
            $display("Starting comparison_test at time %0t", $time);
            
            // Test SLT operation (a < b)
            a = 32'h00000001;
            b = 32'h00000002;
            op = 4'b0111;
            #10;
            
            if (result == 32'h00000001 && zero == 1'b0) begin
                $display("SLT operation test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("SLT operation test FAILED - Expected 0x00000001, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test SLT operation (a >= b)
            a = 32'h00000002;
            b = 32'h00000001;
            op = 4'b0111;
            #10;
            
            if (result == 32'h00000000 && zero == 1'b1) begin
                $display("SLT operation test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("SLT operation test FAILED - Expected 0x00000000, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            $display("Completed comparison_test at time %0t", $time);
        end
    endtask
    
    task boundary_test;
        integer i;
        begin
            $display("Starting boundary_test at time %0t", $time);
            
            // Test with maximum values
            a = 32'hFFFFFFFF;
            b = 32'hFFFFFFFF;
            op = 4'b0000;
            #10;
            
            if (result == 32'hFFFFFFFE && zero == 1'b0) begin
                $display("Boundary max values test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("Boundary max values test FAILED - Expected 0xFFFFFFFE, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test with zero values
            a = 32'h00000000;
            b = 32'h00000000;
            op = 4'b0000;
            #10;
            
            if (result == 32'h00000000 && zero == 1'b1) begin
                $display("Boundary zero values test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("Boundary zero values test FAILED - Expected 0x00000000, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            // Test with negative numbers
            a = 32'h80000000;
            b = 32'h80000000;
            op = 4'b0000;
            #10;
            
            if (result == 32'h00000000 && zero == 1'b1) begin
                $display("Boundary negative numbers test PASSED");
                pass_count = pass_count + 1;
            end else begin
                $display("Boundary negative numbers test FAILED - Expected 0x00000000, got 0x%08h", result);
                fail_count = fail_count + 1;
            end
            
            $display("Completed boundary_test at time %0t", $time);
        end
    endtask
    
    // Main test sequence
    initial begin
        // Initialize counters
        pass_count = 0;
        fail_count = 0;
        
        // Wait for reset to be asserted
        wait(rst_n == 1'b1);
        
        // Run all test cases
        addition_test();
        logical_test();
        shift_test();
        comparison_test();
        boundary_test();
        
        // Display final results
        $display("Test Summary:");
        $display("Total tests passed: %0d", pass_count);
        $display("Total tests failed: %0d", fail_count);
        $display("Total tests run: %0d", pass_count + fail_count);
        
        // Finish simulation
        #100;
        $finish;
    end
    
endmodule