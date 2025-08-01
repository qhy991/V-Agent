module simple_module_tb;

  // Signals
  reg clk;
  reg rst;
  wire [7:0] data_out;

  // Instantiate the module under test
  simple_module uut (
    .clk(clk),
    .rst(rst),
    .data_out(data_out)
  );

  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk; // 10ns period
  end

  // Test sequence
  initial begin
    $dumpfile("simple_module_tb.vcd");
    $dumpvars(0, simple_module_tb);

    // Initialize signals
    rst = 1;
    #10;
    rst = 0;

    // Test case 1: Basic functionality (counting from 0 to 255)
    $display("\n=== Test Case 1: Basic Functionality ===");
    for (int i = 0; i < 256; i = i + 1) begin
      #10;
      $display("Cycle %0d: data_out = %0d", i, data_out);
      if (i == 0) begin
        assert (data_out == 0) else $error("Test Case 1 - Expected 0, got %0d", data_out);
      end else begin
        assert (data_out == i) else $error("Test Case 1 - Expected %0d, got %0d", i, data_out);
      end
    end

    // Test case 2: Reset during counting
    $display("\n=== Test Case 2: Reset During Counting ===");
    rst = 1;
    #10;
    rst = 0;
    #10;
    $display("After reset, data_out = %0d", data_out);
    assert (data_out == 0) else $error("Test Case 2 - Expected 0, got %0d", data_out);

    // Test case 3: Boundary value (max count)
    $display("\n=== Test Case 3: Boundary Value (Max Count) ===");
    for (int i = 0; i < 256; i = i + 1) begin
      #10;
    end
    $display("Final data_out = %0d", data_out);
    assert (data_out == 255) else $error("Test Case 3 - Expected 255, got %0d", data_out);

    // Test case 4: Random values (simulate random input)
    $display("\n=== Test Case 4: Random Values ===");
    // Since this is a simple counter, random inputs are not applicable. Instead, simulate a few random cycles.
    for (int i = 0; i < 10; i = i + 1) begin
      #10;
      $display("Random cycle %0d: data_out = %0d", i, data_out);
    end

    // Test case 5: Performance (time to reach max value)
    $display("\n=== Test Case 5: Performance (Time to Max Count) ===");
    rst = 1;
    #10;
    rst = 0;
    #10;
    $display("Starting count...");
    for (int i = 0; i < 256; i = i + 1) begin
      #10;
    end
    $display("Reached max count of 255 in %0d cycles (2560ns)", 256);

    $finish;
  end

endmodule