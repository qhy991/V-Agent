`timescale 1ns / 1ps

module counter_4bit_tb;

// Inputs
reg clk;
reg reset_n;
reg enable;

// Outputs
wire [3:0] count;

// Instantiate the Unit Under Test (UUT)
counter_4bit uut (
    .clk(clk), 
    .reset_n(reset_n), 
    .enable(enable), 
    .count(count)
);

// Clock generation
always begin
    #5 clk = ~clk;
end

// Test procedure
initial begin
    // Initialize inputs
    clk = 0;
    reset_n = 0;
    enable = 0;
    
    // Display header
    $display("Time\tclk\treset_n\tenable\tcount");
    $monitor("%0t\t%b\t%b\t%b\t%0d", $time, clk, reset_n, enable, count);
    
    // Test Case 1: Reset functionality
    #10 reset_n = 1;
    #10 reset_n = 0;  // Assert reset
    #10 reset_n = 1;  // Deassert reset
    #10;
    
    // Test Case 2: Enable functionality
    enable = 1;
    #100;  // Let it count for a while
    
    // Test Case 3: Disable functionality
    enable = 0;
    #50;   // Let it stay constant
    
    // Test Case 4: Wraparound functionality
    enable = 1;
    #400;  // Let it wrap around
    
    // End simulation
    $finish;
end

endmodule