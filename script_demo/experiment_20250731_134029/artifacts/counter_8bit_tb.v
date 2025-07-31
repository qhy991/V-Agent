module counter_8bit_tb;
    reg clk, reset, enable, load;
    reg [7:0] load_data;
    wire [7:0] count;
    
    counter_8bit uut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .load_data(load_data),
        .load(load),
        .count(count)
    );
    
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    initial begin
        $dumpfile("counter_8bit.vcd");
        $dumpvars(0, counter_8bit_tb);
        
        // Reset test
        reset = 1; enable = 0; load = 0; load_data = 0;
        #10 reset = 0;
        
        // Count test
        enable = 1;
        #100;
        
        // Load test
        enable = 0;
        load_data = 8'hFF;
        load = 1;
        #10 load = 0;
        enable = 1;
        #50;
        
        $display("Counter test completed");
        $finish;
    end
endmodule