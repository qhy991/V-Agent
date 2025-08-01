module alu_tb();

  // Inputs
  reg [31:0] a;
  reg [31:0] b;

  // Outputs
  wire [31:0] result;

  // Instantiate the Unit Under Test (UUT)
  alu uut (
    .a(a),
    .b(b),
    .result(result)
  );

  // Clock generation (if needed, though not used in this ALU)
  reg clk = 0;
  always #5 clk = ~clk; // 10ns period clock

  // Reset sequence
  initial begin
    $dumpfile("alu_tb.vcd");
    $dumpvars(0, alu_tb);

    // Initialize inputs
    a = 32'h0;
    b = 32'h0;

    // Apply reset (not used in this ALU, but for completeness)
    #10;

    // Run test cases
    run_test_case("Basic Addition", 32'h12345678, 32'h87654321, 32'h99999999);
    run_test_case("Maximum Value", 32'hFFFFFFFF, 32'h00000001, 32'h100000000);
    run_test_case("Minimum Value", 32'h00000000, 32'h00000000, 32'h00000000);
    run_test_case("Overflow Test", 32'hFFFFFFFF, 32'hFFFFFFFF, 32'hFFFFFFFE);
    run_test_case("Random Values", 32'hAABBCCDD, 32'h11223344, 32'hBBD00021);
    run_test_case("Zero Input", 32'h00000000, 32'h00000000, 32'h00000000);
    run_test_case("Negative Result", 32'h00000001, 32'h00000002, 32'h00000003);

    // Finish simulation
    #100;
    $finish;
  end

  // Task to run a test case
  task run_test_case;
    input string test_name;
    input [31:0] a_val;
    input [31:0] b_val;
    input [31:0] expected_result;

    begin
      // Set inputs
      a = a_val;
      b = b_val;

      // Wait for the ALU to compute the result
      #1;

      // Check if the result matches the expected value
      if (result === expected_result) begin
        $display("[PASS] %s: a=0x%h, b=0x%h, result=0x%h", test_name, a_val, b_val, result);
      end else begin
        $display("[FAIL] %s: a=0x%h, b=0x%h, expected=0x%h, got=0x%h", test_name, a_val, b_val, expected_result, result);
      end
    end
  endtask

endmodule