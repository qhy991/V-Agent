`timescale 1ns/1ps

module tb_alu_32bit;

    // Testbench signals
    reg  [31:0] a, b;
    reg  [3:0]  op;
    wire [31:0] result;
    wire        zero;
    
    // Clock and reset signals
    reg         clk;
    reg         rst_n;
    
    // Test control signals
    integer     i;
    integer     test_case;
    integer     error_count;
    
    // DUT instantiation
    alu_32bit uut (
        .a      (a),
        .b      (b),
        .op     (op),
        .result (result),
        .zero   (zero)
    );
    
    // Clock generation
    always #5 clk = ~clk; // 10ns period clock
    
    // Reset generation
    initial begin
        clk = 0;
        rst_n = 0;
        #10 rst_n = 1;
    end
    
    // Test case definitions
    parameter ADDITION_TEST                   = 1;
    parameter SUBTRACTION_TEST                = 2;
    parameter AND_OPERATION_TEST              = 3;
    parameter OR_OPERATION_TEST               = 4;
    parameter XOR_OPERATION_TEST              = 5;
    parameter LEFT_SHIFT_TEST                 = 6;
    parameter RIGHT_SHIFT_TEST                = 7;
    parameter ARITHMETIC_RIGHT_SHIFT_TEST     = 8;
    parameter ZERO_RESULT_TEST                = 9;
    parameter BOUNDARY_VALUES_TEST            = 10;
    
    // Testbench main process
    initial begin
        $dumpfile("alu_32bit.vcd");
        $dumpvars(0, tb_alu_32bit);
        
        error_count = 0;
        test_case = 0;
        
        $display("Starting ALU 32-bit Testbench at time %0t", $time);
        
        // Addition test
        test_case = ADDITION_TEST;
        $display("Running Addition Test...");
        addition_test();
        
        // Subtraction test
        test_case = SUBTRACTION_TEST;
        $display("Running Subtraction Test...");
        subtraction_test();
        
        // AND operation test
        test_case = AND_OPERATION_TEST;
        $display("Running AND Operation Test...");
        and_operation_test();
        
        // OR operation test
        test_case = OR_OPERATION_TEST;
        $display("Running OR Operation Test...");
        or_operation_test();
        
        // XOR operation test
        test_case = XOR_OPERATION_TEST;
        $display("Running XOR Operation Test...");
        xor_operation_test();
        
        // Left shift test
        test_case = LEFT_SHIFT_TEST;
        $display("Running Left Shift Test...");
        left_shift_test();
        
        // Right shift test
        test_case = RIGHT_SHIFT_TEST;
        $display("Running Right Shift Test...");
        right_shift_test();
        
        // Arithmetic right shift test
        test_case = ARITHMETIC_RIGHT_SHIFT_TEST;
        $display("Running Arithmetic Right Shift Test...");
        arithmetic_right_shift_test();
        
        // Zero result test
        test_case = ZERO_RESULT_TEST;
        $display("Running Zero Result Test...");
        zero_result_test();
        
        // Boundary values test
        test_case = BOUNDARY_VALUES_TEST;
        $display("Running Boundary Values Test...");
        boundary_values_test();
        
        // Final report
        $display("Testbench completed at time %0t", $time);
        $display("Total errors detected: %0d", error_count);
        
        if (error_count == 0) begin
            $display("All tests passed successfully!");
        end else begin
            $display("Some tests failed with %0d errors.", error_count);
        end
        
        $finish;
    end
    
    // Monitor for signal changes
    initial begin
        $monitor("Time=%0t: a=0x%08h, b=0x%08h, op=0x%01h, result=0x%08h, zero=%0b", 
                 $time, a, b, op, result, zero);
    end
    
    // Addition test
    task addition_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'h00000001 + j;
                b = 32'h00000002 + j;
                op = 4'b0000;
                #10;
                if (result != (a + b)) begin
                    $display("Addition test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, (a + b), result);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Subtraction test
    task subtraction_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'h00000010 + j;
                b = 32'h00000005 + j;
                op = 4'b0001;
                #10;
                if (result != (a - b)) begin
                    $display("Subtraction test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, (a - b), result);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // AND operation test
    task and_operation_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'hAAAA0000 + j;
                b = 32'h0000FFFF + j;
                op = 4'b0010;
                #10;
                if (result != (a & b)) begin
                    $display("AND operation test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, (a & b), result);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // OR operation test
    task or_operation_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'hAAAA0000 + j;
                b = 32'h0000FFFF + j;
                op = 4'b0011;
                #10;
                if (result != (a | b)) begin
                    $display("OR operation test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, (a | b), result);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // XOR operation test
    task xor_operation_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'hAAAA0000 + j;
                b = 32'h0000FFFF + j;
                op = 4'b0100;
                #10;
                if (result != (a ^ b)) begin
                    $display("XOR operation test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, (a ^ b), result);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Left shift test
    task left_shift_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'h00000001 + j;
                b = 32'h00000003 + j;
                op = 4'b0101;
                #10;
                if (result != (a << b[4:0])) begin
                    $display("Left shift test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, (a << b[4:0]), result);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Right shift test
    task right_shift_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'h00000010 + j;
                b = 32'h00000002 + j;
                op = 4'b0110;
                #10;
                if (result != (a >> b[4:0])) begin
                    $display("Right shift test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, (a >> b[4:0]), result);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Arithmetic right shift test
    task arithmetic_right_shift_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'h80000000 + j;
                b = 32'h00000003 + j;
                op = 4'b0111;
                #10;
                if (result != ($signed(a) >>> b[4:0])) begin
                    $display("Arithmetic right shift test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, ($signed(a) >>> b[4:0]), result);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Zero result test
    task zero_result_test;
        integer j;
        begin
            for (j = 0; j < 5; j = j + 1) begin
                a = 32'h00000000;
                b = 32'h00000000;
                op = 4'b0000; // Addition
                #10;
                if (result != 32'h00000000) begin
                    $display("Zero result test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, 32'h00000000, result);
                    error_count = error_count + 1;
                end
                if (zero != 1'b1) begin
                    $display("Zero flag test failed at time %0t: Expected zero=1'b1, Got zero=%0b", 
                             $time, zero);
                    error_count = error_count + 1;
                end
                
                a = 32'h00000001;
                b = 32'h00000001;
                op = 4'b0001; // Subtraction
                #10;
                if (result != 32'h00000000) begin
                    $display("Zero result test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                             $time, 32'h00000000, result);
                    error_count = error_count + 1;
                end
                if (zero != 1'b1) begin
                    $display("Zero flag test failed at time %0t: Expected zero=1'b1, Got zero=%0b", 
                             $time, zero);
                    error_count = error_count + 1;
                end
            end
        end
    endtask
    
    // Boundary values test
    task boundary_values_test;
        integer j;
        begin
            // Test maximum values
            a = 32'hFFFFFFFF;
            b = 32'h00000001;
            op = 4'b0000; // Addition
            #10;
            if (result != 32'h00000000) begin
                $display("Boundary test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                         $time, 32'h00000000, result);
                error_count = error_count + 1;
            end
            
            // Test minimum values
            a = 32'h80000000;
            b = 32'h80000000;
            op = 4'b0001; // Subtraction
            #10;
            if (result != 32'h00000000) begin
                $display("Boundary test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                         $time, 32'h00000000, result);
                error_count = error_count + 1;
            end
            
            // Test zero values
            a = 32'h00000000;
            b = 32'h00000000;
            op = 4'b0010; // AND
            #10;
            if (result != 32'h00000000) begin
                $display("Boundary test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                         $time, 32'h00000000, result);
                error_count = error_count + 1;
            end
            
            // Test all ones
            a = 32'hFFFFFFFF;
            b = 32'hFFFFFFFF;
            op = 4'b0011; // OR
            #10;
            if (result != 32'hFFFFFFFF) begin
                $display("Boundary test failed at time %0t: Expected 0x%08h, Got 0x%08h", 
                         $time, 32'hFFFFFFFF, result);
                error_count = error_count + 1;
            end
        end
    endtask

endmodule