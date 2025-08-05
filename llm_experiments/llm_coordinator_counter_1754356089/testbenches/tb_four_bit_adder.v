`timescale 1ns / 1ps

module tb_four_bit_adder;

    // Inputs
    reg [3:0] a;
    reg [3:0] b;

    // Outputs
    wire [3:0] sum;
    wire cout;

    // Instantiate the Unit Under Test (UUT)
    four_bit_adder uut (
        .a(a),
        .b(b),
        .sum(sum),
        .cout(cout)
    );

    initial begin
        // Display the header
        $display("Time\ta\t\tb\t\tsum\t\tcout");

        // Test case 1: 基本加法测试：5 + 3 = 8
        a = 4'd5;
        b = 4'd3;
        #10;
        $display("%0t\t%b(%0d)\t\t%b(%0d)\t\t%b(%0d)\t\t%b", $time, a, a, b, b, sum, sum, cout);

        // Test case 2: 进位测试：15 + 1 = 0，cout=1
        a = 4'd15;
        b = 4'd1;
        #10;
        $display("%0t\t%b(%0d)\t\t%b(%0d)\t\t%b(%0d)\t\t%b", $time, a, a, b, b, sum, sum, cout);

        // Test case 3: 边界值测试：0 + 0 = 0
        a = 4'd0;
        b = 4'd0;
        #10;
        $display("%0t\t%b(%0d)\t\t%b(%0d)\t\t%b(%0d)\t\t%b", $time, a, a, b, b, sum, sum, cout);

        // Test case 4: 边界值测试：15 + 15 = 14，cout=1
        a = 4'd15;
        b = 4'd15;
        #10;
        $display("%0t\t%b(%0d)\t\t%b(%0d)\t\t%b(%0d)\t\t%b", $time, a, a, b, b, sum, sum, cout);

        // Test case 5: 零值测试：7 + 0 = 7
        a = 4'd7;
        b = 4'd0;
        #10;
        $display("%0t\t%b(%0d)\t\t%b(%0d)\t\t%b(%0d)\t\t%b", $time, a, a, b, b, sum, sum, cout);

        // Finish simulation
        $finish;
    end

endmodule