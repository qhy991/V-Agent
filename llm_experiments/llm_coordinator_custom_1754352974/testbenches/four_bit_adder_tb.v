module four_bit_adder_tb;

    // Inputs
    reg [3:0] a;
    reg [3:0] b;
    reg cin;

    // Outputs
    wire [3:0] sum;
    wire cout;

    // Instantiate the Unit Under Test (UUT)
    four_bit_adder uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    // Testbench stimulus
    initial begin
        // Initialize inputs
        a = 0;
        b = 0;
        cin = 0;

        // Display header
        $display("Time\tA\tB\tCin\tSum\tCout\tExpected_Sum\tExpected_Cout\tResult");

        // Test case 1: 0 + 0 + 0
        #10;
        check_result(4'd0, 1'b0);

        // Test case 2: 1 + 0 + 0
        a = 1;
        b = 0;
        cin = 0;
        #10;
        check_result(4'd1, 1'b0);

        // Test case 3: 7 + 3 + 0
        a = 7;
        b = 3;
        cin = 0;
        #10;
        check_result(4'd10, 1'b0);

        // Test case 4: 8 + 8 + 0 (carry out)
        a = 8;
        b = 8;
        cin = 0;
        #10;
        check_result(4'd0, 1'b1);

        // Test case 5: 15 + 15 + 0 (maximum values)
        a = 15;
        b = 15;
        cin = 0;
        #10;
        check_result(4'd14, 1'b1);

        // Test case 6: 7 + 8 + 1 (carry in)
        a = 7;
        b = 8;
        cin = 1;
        #10;
        check_result(4'd0, 1'b1);

        // Test case 7: 0 + 0 + 1 (carry in only)
        a = 0;
        b = 0;
        cin = 1;
        #10;
        check_result(4'd1, 1'b0);

        // Test case 8: 15 + 0 + 1 (carry in with maximum a)
        a = 15;
        b = 0;
        cin = 1;
        #10;
        check_result(4'd0, 1'b1);

        // Exhaustive test: iterate through all possible inputs
        exhaustive_test();

        // Finish simulation
        #10;
        $display("\nSimulation completed.");
        $finish;
    end

    // Task to check results
    task check_result;
        input [3:0] expected_sum;
        input expected_cout;
        begin
            if (sum === expected_sum && cout === expected_cout) begin
                $display("%0t\t%0d\t%0d\t%0b\t%0d\t%0b\t%0d\t\t%0b\t\tPASS", 
                         $time, a, b, cin, sum, cout, expected_sum, expected_cout);
            end else begin
                $display("%0t\t%0d\t%0d\t%0b\t%0d\t%0b\t%0d\t\t%0b\t\tFAIL", 
                         $time, a, b, cin, sum, cout, expected_sum, expected_cout);
            end
        end
    endtask

    // Exhaustive test procedure
    task exhaustive_test;
        integer i, j;
        reg [3:0] exp_sum;
        reg exp_cout;
        integer error_count;
        begin
            error_count = 0;
            $display("\nRunning exhaustive test for all input combinations...");
            
            // Loop through all possible values of a, b, and cin
            for (i = 0; i < 16; i = i + 1) begin
                for (j = 0; j < 16; j = j + 1) begin
                    // Test with cin = 0
                    a = i;
                    b = j;
                    cin = 0;
                    #1;
                    
                    // Calculate expected results
                    exp_sum = (i + j) & 4'hF;  // Lower 4 bits
                    exp_cout = (i + j) > 15;   // Carry out if sum > 15
                    
                    if (!(sum === exp_sum && cout === exp_cout)) begin
                        error_count = error_count + 1;
                        $display("ERROR: a=%0d, b=%0d, cin=%0b => sum=%0d, cout=%0b (expected: sum=%0d, cout=%0b)", 
                                 a, b, cin, sum, cout, exp_sum, exp_cout);
                    end
                    
                    // Test with cin = 1
                    cin = 1;
                    #1;
                    
                    // Calculate expected results with carry in
                    exp_sum = (i + j + 1) & 4'hF;  // Lower 4 bits
                    exp_cout = (i + j + 1) > 15;   // Carry out if sum > 15
                    
                    if (!(sum === exp_sum && cout === exp_cout)) begin
                        error_count = error_count + 1;
                        $display("ERROR: a=%0d, b=%0d, cin=%0b => sum=%0d, cout=%0b (expected: sum=%0d, cout=%0b)", 
                                 a, b, cin, sum, cout, exp_sum, exp_cout);
                    end
                end
            end
            
            if (error_count == 0) begin
                $display("Exhaustive test PASSED: All 512 test cases passed");
            end else begin
                $display("Exhaustive test FAILED: %0d errors found", error_count);
            end
        end
    endtask

endmodule