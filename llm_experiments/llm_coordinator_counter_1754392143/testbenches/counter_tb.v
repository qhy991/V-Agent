`timescale 1ns/1ps

module counter_tb;

reg clk;
reg rst_n;
reg en;
wire [3:0] count;

// Instantiate the counter module
counter uut (
    .clk(clk),
    .rst_n(rst_n),
    .en(en),
    .count(count)
);

// Clock generation
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// Test sequence
initial begin
    // Initialize inputs
    rst_n = 0;
    en = 0;
    #15 rst_n = 1; // Release reset

    #10 en = 1; // Enable counting
    #80 en = 0; // Disable counting
    #20 en = 1; // Re-enable counting
    #50 $finish;
end

endmodule