module and_gate_tb;
    reg a, b;
    wire y;
    
    and_gate uut (.a(a), .b(b), .y(y));
    
    initial begin
        $display("Testing AND gate");
        a = 0; b = 0; #10; $display("0 & 0 = %b", y);
        a = 0; b = 1; #10; $display("0 & 1 = %b", y);
        a = 1; b = 0; #10; $display("1 & 0 = %b", y);
        a = 1; b = 1; #10; $display("1 & 1 = %b", y);
        $finish;
    end
endmodule