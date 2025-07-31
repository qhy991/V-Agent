module instantiation_tb();

// Inputs
reg a0;
reg a1;
reg b0;
reg b1;
reg carry_in;

// Outputs
wire [1:0] sum;
wire carry_out;

// Instantiate the Unit Under Test (UUT)
adder_2bit uut (
    .a({a1, a0}),
    .b({b1, b0}),
    .carry_in(carry_in),
    .sum(sum),
    .carry_out(carry_out)
);

// Clock generation (if needed)
initial begin
    $dumpfile("instantiation_tb.vcd");
    $dumpvars(0, instantiation_tb);
    #10;
end

// Test sequence
initial begin
    // Initialize inputs
    a0 = 0;
    a1 = 0;
    b0 = 0;
    b1 = 0;
    carry_in = 0;

    // Test case 1: Basic addition with no carry in
    #10;
    a0 = 0; a1 = 0; b0 = 0; b1 = 0; carry_in = 0;
    $display("Test Case 1: a=00, b=00, carry_in=0 -> sum=00, carry_out=0");

    // Test case 2: Add 01 + 01 with no carry in
    #10;
    a0 = 1; a1 = 0; b0 = 1; b1 = 0; carry_in = 0;
    $display("Test Case 2: a=01, b=01, carry_in=0 -> sum=10, carry_out=0");

    // Test case 3: Add 11 + 11 with no carry in
    #10;
    a0 = 1; a1 = 1; b0 = 1; b1 = 1; carry_in = 0;
    $display("Test Case 3: a=11, b=11, carry_in=0 -> sum=10, carry_out=1");

    // Test case 4: Add 11 + 00 with carry in 1
    #10;
    a0 = 0; a1 = 1; b0 = 0; b1 = 1; carry_in = 1;
    $display("Test Case 4: a=10, b=10, carry_in=1 -> sum=01, carry_out=1");

    // Test case 5: Add 01 + 11 with carry in 1
    #10;
    a0 = 1; a1 = 0; b0 = 1; b1 = 1; carry_in = 1;
    $display("Test Case 5: a=01, b=11, carry_in=1 -> sum=01, carry_out=1");

    // Test case 6: Add 11 + 11 with carry in 1
    #10;
    a0 = 1; a1 = 1; b0 = 1; b1 = 1; carry_in = 1;
    $display("Test Case 6: a=11, b=11, carry_in=1 -> sum=10, carry_out=1");

    // Test case 7: Random test case
    #10;
    a0 = $random % 2;
    a1 = $random % 2;
    b0 = $random % 2;
    b1 = $random % 2;
    carry_in = $random % 2;
    $display("Test Case 7: Random input: a=%b, b=%b, carry_in=%b", {a1,a0}, {b1,b0}, carry_in);

    // End simulation
    #10;
    $finish;
end

endmodule