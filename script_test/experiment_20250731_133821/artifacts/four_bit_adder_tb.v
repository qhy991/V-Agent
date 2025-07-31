module four_bit_adder_tb;
    reg [3:0] a, b;
    reg cin;
    wire [3:0] sum;
    wire cout;
    
    four_bit_adder uut (
        .a(a), .b(b), .cin(cin),
        .sum(sum), .cout(cout)
    );
    
    initial begin
        $dumpfile("four_bit_adder.vcd");
        $dumpvars(0, four_bit_adder_tb);
        
        // Comprehensive test cases
        $display("Starting 4-bit adder tests...");
        
        a = 4'b0000; b = 4'b0000; cin = 0; #10;
        $display("Test: %b + %b + %b = %b (cout=%b)", a, b, cin, sum, cout);
        
        a = 4'b0101; b = 4'b1010; cin = 0; #10;
        $display("Test: %b + %b + %b = %b (cout=%b)", a, b, cin, sum, cout);
        
        a = 4'b1111; b = 4'b0001; cin = 0; #10;
        $display("Test: %b + %b + %b = %b (cout=%b)", a, b, cin, sum, cout);
        
        a = 4'b1111; b = 4'b1111; cin = 1; #10;
        $display("Test: %b + %b + %b = %b (cout=%b)", a, b, cin, sum, cout);
        
        $display("All tests completed.");
        $finish;
    end
endmodule