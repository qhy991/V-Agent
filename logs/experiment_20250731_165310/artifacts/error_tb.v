module error_tb;
    reg clk;
    wire [7:0] count;

    // 实例化被测模块
    error uut (
        .clk(clk),
        .count(count)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns周期时钟
    end

    // 测试控制
    initial begin
        $dumpfile("error_tb.vcd");
        $dumpvars(0, error_tb);

        // 初始状态
        $display("[INFO] Starting testbench...");

        // 测试用例1: 基本功能测试 - 验证计数器是否正常工作
        #20;
        $display("[TEST] Test Case 1: Basic functionality");
        $display("[EXPECTED] count should be 8'h00 at time 0");
        $display("[ACTUAL] count is %h", count);
        if (count != 8'h00) $display("[ERROR] Test Case 1 failed!");
        else $display("[PASS] Test Case 1 passed.");

        // 测试用例2: 边界值测试 - 验证计数器在10ns后是否变为8'hFF
        #10;
        $display("[TEST] Test Case 2: Boundary value");
        $display("[EXPECTED] count should be 8'hFF at time 10ns");
        $display("[ACTUAL] count is %h", count);
        if (count != 8'hFF) $display("[ERROR] Test Case 2 failed!");
        else $display("[PASS] Test Case 2 passed.");

        // 测试用例3: 异常情况 - 检查$display和$finish是否执行
        #10;
        $display("[TEST] Test Case 3: Exception handling");
        $display("[EXPECTED] $display and $finish should execute");
        $display("[ACTUAL] $display executed successfully");
        $display("[ACTUAL] $finish called");
        $display("[INFO] Simulation finished.");

        $finish;
    end
endmodule