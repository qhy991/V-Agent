module simple_adder_tb;

    reg [3:0] a;
    reg [3:0] b;
    wire [4:0] sum;

    // Instantiate the Unit Under Test (UUT)
    simple_adder uut (
        .a(a),
        .b(b),
        .sum(sum)
    );

    initial begin
        $monitor("Time %t: a = %b, b = %b, sum = %b", $time, a, b, sum);

        // Test case 1: a = 0, b = 0
        a = 4'b0000;
        b = 4'b0000;
        #10;

        // Test case 2: a = 5, b = 3
        a = 4'b0101;
        b = 4'b0011;
        #10;

        // Test case 3: a = 15, b = 15
        a = 4'b1111;
        b = 4'b1111;
        #10;

        // Test case 4: a = 10, b = 5
        a = 4'b1010;
        b = 4'b0101;
        #10;

        // Test case 5: a = 7, b = 8
        a = 4'b0111;
        b = 4'b1000;
        #10;

        $finish;
    end

endmodule