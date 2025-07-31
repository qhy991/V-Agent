module adder_4bit_tb;

  reg [3:0] a;
  reg [3:0] b;
  wire [3:0] sum;
  wire carry;

  // 实例化被测模块
  adder_4bit uut (
    .a(a),
    .b(b),
    .sum(sum),
    .carry(carry)
  );

  initial begin
    $dumpfile("adder_4bit_tb.vcd");
    $dumpvars(0, adder_4bit_tb);

    // 测试用例1: 基本功能测试 (0 + 0 = 0, carry=0)
    a = 4'b0000;
    b = 4'b0000;
    #10;
    $display("Test Case 1: a=0000, b=0000 -> sum=0000, carry=0");

    // 测试用例2: 基本功能测试 (1 + 1 = 2, carry=0)
    a = 4'b0001;
    b = 4'b0001;
    #10;
    $display("Test Case 2: a=0001, b=0001 -> sum=0010, carry=0");

    // 测试用例3: 边界值测试 (最大值相加: 15 + 15 = 30, carry=1)
    a = 4'b1111;
    b = 4'b1111;
    #10;
    $display("Test Case 3: a=1111, b=1111 -> sum=1110, carry=1");

    // 测试用例4: 边界值测试 (最小值相加: 0 + 0 = 0, carry=0)
    a = 4'b0000;
    b = 4'b0000;
    #10;
    $display("Test Case 4: a=0000, b=0000 -> sum=0000, carry=0");

    // 测试用例5: 随机测试 (随机输入)
    a = 4'b1010;
    b = 4'b0101;
    #10;
    $display("Test Case 5: a=1010, b=0101 -> sum=1111, carry=0");

    // 测试用例6: 随机测试 (随机输入)
    a = 4'b0111;
    b = 4'b1001;
    #10;
    $display("Test Case 6: a=0111, b=1001 -> sum=0000, carry=1");

    // 测试用例7: 异常情况 (输入超出范围，但此处为4位输入，不适用)
    $display("Test Case 7: No abnormal input for 4-bit inputs");

    // 测试用例8: 性能测试 (连续多个输入测试)
    for (integer i = 0; i < 16; i = i + 1) begin
      a = i;
      b = i;
      #10;
      $display("Test Case 8: a=%b, b=%b -> sum=%b, carry=%b", a, b, sum, carry);
    end

    $finish;
  end

endmodule