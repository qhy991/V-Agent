
module simple_adder_tb;
    reg [7:0] a, b;
    wire [8:0] sum;
    
    simple_adder uut (.a(a), .b(b), .sum(sum));
    
    initial begin
        $dumpfile("simple_adder.vcd");
        $dumpvars(0, simple_adder_tb);
        
        a = 8'd10; b = 8'd20; #10;
        a = 8'd255; b = 8'd1; #10;
        a = 8'd128; b = 8'd128; #10;
        
        $finish;
    end
endmodule
