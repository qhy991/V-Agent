module simple_adder_tb;
    reg [3:0] a, b;
    reg cin;
    wire [3:0] sum;
    wire cout;
    
    simple_adder uut (
        .a(a),
        .b(b), 
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );
    
    initial begin
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, simple_adder_tb);
        
        // Test cases
        a = 4'b0001; b = 4'b0010; cin = 0; #10;
        $display("Test 1: %d + %d + %d = %d (cout=%d)", a, b, cin, sum, cout);
        
        a = 4'b1111; b = 4'b0001; cin = 0; #10;
        $display("Test 2: %d + %d + %d = %d (cout=%d)", a, b, cin, sum, cout);
        
        a = 4'b1111; b = 4'b1111; cin = 1; #10;
        $display("Test 3: %d + %d + %d = %d (cout=%d)", a, b, cin, sum, cout);
        
        $finish;
    end
endmodule