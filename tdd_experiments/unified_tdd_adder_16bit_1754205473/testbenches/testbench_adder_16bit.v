module tb_adder_16bit;

    reg [15:0] a, b;
    reg cin;
    wire [15:0] sum;
    wire cout;
    wire overflow;

    // Instantiate DUT
    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    initial begin
        $dumpfile("adder_16bit.vcd");
        $dumpvars(0, tb_adder_16bit);

        // Test case 1: Positive numbers
        a = 16'h1234; b = 16'h5678; cin = 1'b0;
        #10;

        // Test case 2: Negative overflow
        a = 16'h8000; b = 16'h8000; cin = 1'b0;
        #10;

        // Test case 3: Max positive + min negative
        a = 16'hFFFF; b = 16'h8000; cin = 1'b0;
        #10;

        // Test case 4: All ones with cin=1
        a = 16'hFFFF; b = 16'hFFFF; cin = 1'b1;
        #10;

        // Test case 5: Zero with cin=1
        a = 16'h0000; b = 16'h0000; cin = 1'b1;
        #10;

        $finish;
    end

    initial begin
        $monitor("Time=%0t | a=0x%h, b=0x%h, cin=%b | sum=0x%h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end

endmodule