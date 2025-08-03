module test_adder_16bit;
    reg [15:0] a;
    reg [15:0] b;
    reg cin;
    wire [15:0] sum;
    wire cout;
    wire overflow;

    adder_16bit uut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout),
        .overflow(overflow)
    );

    initial begin
        // 基本加法测试
        a = 16'h0000; b = 16'h0000; cin = 1'b0; #10;
        a = 16'h0001; b = 16'h0001; cin = 1'b0; #10;
        a = 16'hFFFF; b = 16'hFFFF; cin = 1'b0; #10;
        a = 16'h8000; b = 16'h8000; cin = 1'b0; #10;
        a = 16'h7FFF; b = 16'h7FFF; cin = 1'b0; #10;
        a = 16'h0000; b = 16'h0000; cin = 1'b1; #10;
        a = 16'h0001; b = 16'h0001; cin = 1'b1; #10;
        a = 16'hFFFF; b = 16'hFFFF; cin = 1'b1; #10;
        a = 16'h8000; b = 16'h8000; cin = 1'b1; #10;
        a = 16'h7FFF; b = 16'h7FFF; cin = 1'b1; #10;
        $display("Test completed");
        $finish;
    end

    initial begin
        $monitor("Time=%t, a=0x%04h, b=0x%04h, cin=%b, sum=0x%04h, cout=%b, overflow=%b", $time, a, b, cin, sum, cout, overflow);
    end
endmodule