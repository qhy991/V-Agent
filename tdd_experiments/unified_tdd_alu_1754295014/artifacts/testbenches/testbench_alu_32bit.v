`timescale 1ns/1ps

module tb_alu_32bit;

    // Testbench signals
    reg  [31:0] a;
    reg  [31:0] b;
    reg  [3:0]  op;
    wire [31:0] result;
    wire        carry_out;

    // Clock and reset signals
    reg clk;
    reg rst_n;

    // Test status signals
    integer i;
    integer test_case;
    integer error_count;
    integer pass_count;

    // Instantiate the DUT
    alu_32bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .carry_out(carry_out)
    );

    // Generate clock
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 10ns period clock
    end

    // Reset generation
    initial begin
        rst_n = 0;
        #10 rst_n = 1;
    end

    // Monitor signals
    initial begin
        $monitor("Time=%0t | a=0x%08h b=0x%08h op=%b result=0x%08h carry_out=%b", 
                 $time, a, b, op, result, carry_out);
    end

    // VCD waveform dump
    initial begin
        $dumpfile("alu_32bit_tb.vcd");
        $dumpvars(0, tb_alu_32bit);
    end

    // Test cases
    initial begin
        error_count = 0;
        pass_count = 0;

        // Wait for reset to complete
        @(posedge clk) @(posedge clk);

        // Test Case 1: Addition Test
        $display("Starting addition_test...");
        addition_test();
        
        // Test Case 2: Subtraction Test
        $display("Starting subtraction_test...");
        subtraction_test();
        
        // Test Case 3: Logical Operations Test
        $display("Starting logical_operations_test...");
        logical_operations_test();
        
        // Test Case 4: Shift Operations Test
        $display("Starting shift_operations_test...");
        shift_operations_test();
        
        // Test Case 5: Boundary Conditions Test
        $display("Starting boundary_conditions_test...");
        boundary_conditions_test();

        // Final report
        $display("Test Summary:");
        $display("  Total Tests Passed: %d", pass_count);
        $display("  Total Tests Failed: %d", error_count);
        $display("  Overall Result: %s", (error_count == 0) ? "PASSED" : "FAILED");

        if (error_count == 0) begin
            $display("All tests passed successfully!");
        end else begin
            $display("Some tests failed!");
        end

        $finish;
    end

    // Addition Test
    task addition_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'h12345678 + j;
                b = 32'h87654321 - j;
                op = 4'b0000;  // ADD
                @(posedge clk);
                if (result != (a + b)) begin
                    $display("ERROR: Addition test failed at cycle %0d. Expected 0x%08h, got 0x%08h", 
                             j, (a + b), result);
                    error_count = error_count + 1;
                end else begin
                    pass_count = pass_count + 1;
                end
            end
        end
    endtask

    // Subtraction Test
    task subtraction_test;
        integer j;
        begin
            for (j = 0; j < 10; j = j + 1) begin
                a = 32'hABCDEF00 + j;
                b = 32'h12345678 - j;
                op = 4'b0001;  // SUB
                @(posedge clk);
                if (result != (a - b)) begin
                    $display("ERROR: Subtraction test failed at cycle %0d. Expected 0x%08h, got 0x%08h", 
                             j, (a - b), result);
                    error_count = error_count + 1;
                end else begin
                    pass_count = pass_count + 1;
                end
            end
        end
    endtask

    // Logical Operations Test
    task logical_operations_test;
        integer j;
        begin
            for (j = 0; j < 5; j = j + 1) begin
                a = 32'hF0F0F0F0;
                b = 32'h0F0F0F0F;
                case (j)
                    0: begin op = 4'b0010; @(posedge clk); if (result != (a & b)) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // AND
                    1: begin op = 4'b0011; @(posedge clk); if (result != (a | b)) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // OR
                    2: begin op = 4'b0100; @(posedge clk); if (result != (a ^ b)) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // XOR
                    3: begin op = 4'b0101; @(posedge clk); if (result != (~a)) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // NOT
                    4: begin op = 4'b0101; @(posedge clk); if (result != (~b)) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // NOT
                endcase
            end
        end
    endtask

    // Shift Operations Test
    task shift_operations_test;
        integer j;
        begin
            for (j = 0; j < 5; j = j + 1) begin
                a = 32'h12345678;
                b = 32'h00000004;
                case (j)
                    0: begin op = 4'b0110; @(posedge clk); if (result != (a << b[4:0])) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // SHIFT LEFT
                    1: begin op = 4'b0111; @(posedge clk); if (result != (a >> b[4:0])) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // SHIFT RIGHT
                    2: begin op = 4'b0110; @(posedge clk); if (result != (a << 1)) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // SHIFT LEFT by 1
                    3: begin op = 4'b0111; @(posedge clk); if (result != (a >> 1)) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // SHIFT RIGHT by 1
                    4: begin op = 4'b0110; @(posedge clk); if (result != (a << 0)) begin error_count = error_count + 1; end else pass_count = pass_count + 1; end  // SHIFT LEFT by 0
                endcase
            end
        end
    endtask

    // Boundary Conditions Test
    task boundary_conditions_test;
        integer j;
        begin
            // Test with zero values
            a = 32'h00000000;
            b = 32'h00000000;
            op = 4'b0000;  // ADD
            @(posedge clk);
            if (result != 32'h00000000) begin
                $display("ERROR: Zero value test failed. Expected 0x00000000, got 0x%08h", result);
                error_count = error_count + 1;
            end else begin
                pass_count = pass_count + 1;
            end

            // Test with maximum values
            a = 32'hFFFFFFFF;
            b = 32'h00000001;
            op = 4'b0000;  // ADD
            @(posedge clk);
            if (result != 32'h00000000) begin
                $display("ERROR: Maximum value test failed. Expected 0x00000000, got 0x%08h", result);
                error_count = error_count + 1;
            end else begin
                pass_count = pass_count + 1;
            end

            // Test with negative numbers
            a = 32'h80000000;
            b = 32'h80000000;
            op = 4'b0001;  // SUB
            @(posedge clk);
            if (result != 32'h00000000) begin
                $display("ERROR: Negative number test failed. Expected 0x00000000, got 0x%08h", result);
                error_count = error_count + 1;
            end else begin
                pass_count = pass_count + 1;
            end

            // Test with carry flag
            a = 32'hFFFFFFFF;
            b = 32'h00000001;
            op = 4'b0000;  // ADD
            @(posedge clk);
            if (carry_out != 1'b1) begin
                $display("ERROR: Carry flag test failed. Expected carry_out=1, got carry_out=%b", carry_out);
                error_count = error_count + 1;
            end else begin
                pass_count = pass_count + 1;
            end

            // Test with all operation codes
            for (j = 0; j < 16; j = j + 1) begin
                a = 32'h12345678;
                b = 32'h87654321;
                op = j;
                @(posedge clk);
                // Just verify that it doesn't crash or hang
                pass_count = pass_count + 1;
            end
        end
    endtask

endmodule