`timescale 1ns / 1ps

module testbench;

// Inputs
reg clk;
reg rst_n;
reg enable;

// Outputs
wire [7:0] count;
wire overflow;

// Instantiate the Unit Under Test (UUT)
simple_counter uut (
    .clk(clk),
    .rst_n(rst_n),
    .enable(enable),
    .count(count),
    .overflow(overflow)
);

// Clock generation
initial begin
    clk = 0;
    forever #5 clk = ~clk; // 10ns period
end

// Test sequence
initial begin
    // Initialize inputs
    rst_n = 0;
    enable = 0;
    
    // Reset
    #10 rst_n = 1;
    
    // Enable counter
    #10 enable = 1;
    
    // Count up to 0xFF
    #160; // 16 cycles of 10ns each
    
    // Disable counter
    #10 enable = 0;
    
    // Wait for some time
    #100;
    
    // Finish simulation
    $finish;
end

// Monitor outputs
initial begin
    $monitor("Time=%0t, count=0x%02h, overflow=%b", $time, count, overflow);
end

endmodule