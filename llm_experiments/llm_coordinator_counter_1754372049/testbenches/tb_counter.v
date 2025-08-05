module tb_counter;

reg clk;
reg rst;
reg en;
wire [7:0] count;

counter uut (
    .clk(clk),
    .rst(rst),
    .en(en),
    .count(count)
);

// Clock generation: 50MHz (20ns period)
always begin
    clk = 0;
    #10;
    clk = 1;
    #10;
end

// Reset sequence: asynchronous active high reset, held for 100ns
initial begin
    rst = 1;
    #100;
    rst = 0;
end

// Test sequence
initial begin
    // Initialize signals
    en = 0;

    // Wait for reset to deassert
    wait(!rst);
    #1;

    // Enable the counter after reset
    en = 1;
    $display("Time: %0t ns, Counter enabled", $time);

    // Monitor count value and display at key points
    repeat(260) begin
        @(posedge clk);
        if ((count == 0) && ($time > 100)) begin
            $display("Time: %0t ns, Counter wrapped to 0, value: %d", $time, count);
        end else if (count == 8'd128) begin
            $display("Time: %0t ns, Counter reached midpoint, value: %d", $time, count);
        end
    end

    // End simulation
    #500 $finish;
end

// Optional waveform dump for debugging
// initial begin
//     $dumpfile("tb_counter.vcd");
//     $dumpvars(0, tb_counter);
// end

endmodule