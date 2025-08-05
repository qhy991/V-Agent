module counter_tb ();

reg clk;
reg rst;
reg en;
wire [7:0] count;

integer fd; // 文件描述符
integer i;

counter uut (
    .clk(clk),
    .rst(rst),
    .en(en),
    .count(count)
);

// 生成时钟信号，周期为10个时间单位
always begin
    #5 clk = ~clk;
end

// 测试过程
initial begin
    // 打开日志文件
    fd = $fopen("counter_tb.log", "w");
    if (fd == 0) begin
        $display("无法打开日志文件 counter_tb.log");
        $finish;
    end

    // 写入日志文件头部信息
    $fwrite(fd, "Counter Testbench Log\n");
    $fwrite(fd, "=====================\n\n");

    // 初始化信号
    clk = 0;
    rst = 1;
    en = 0;

    // 写入初始化信息到日志
    $fwrite(fd, "Time: %0t, 初始化: clk=0, rst=1, en=0\n", $time);

    // 运行一段时间以确保复位生效
    #20;

    // 测试1: 验证复位功能
    $fwrite(fd, "\n测试1: 验证复位功能\n");
    $fwrite(fd, "---------------------\n");
    rst = 1;
    #10;
    if (count == 0) begin
        $fwrite(fd, "PASS: 复位后 count = 0\n");
    end else begin
        $fwrite(fd, "FAIL: 复位后 count != 0 (实际值: %0d)\n", count);
    end

    // 测试2: 验证使能控制
    $fwrite(fd, "\n测试2: 验证使能控制\n");
    $fwrite(fd, "---------------------\n");
    rst = 0;
    en = 0;
    #20;
    if (count == 0) begin
        $fwrite(fd, "PASS: 使能禁用时 count 保持为 0\n");
    end else begin
        $fwrite(fd, "FAIL: 使能禁用时 count 改变 (实际值: %0d)\n", count);
    end

    // 测试3: 验证正常计数操作
    $fwrite(fd, "\n测试3: 验证正常计数操作\n");
    $fwrite(fd, "-------------------------\n");
    en = 1;
    for (i = 0; i < 256; i = i + 1) begin
        #10;
        if (count === i) begin
            $fwrite(fd, "PASS: count = %0d\n", count);
        end else begin
            $fwrite(fd, "FAIL: count = %0d, 期望值 = %0d\n", count, i);
        end
    end

    // 测试4: 验证边界条件 (255 -> 0)
    $fwrite(fd, "\n测试4: 验证边界条件 (255 -> 0)\n");
    $fwrite(fd, "--------------------------------\n");
    #10;
    if (count === 0) begin
        $fwrite(fd, "PASS: 达到 255 后回绕到 0\n");
    end else begin
        $fwrite(fd, "FAIL: 达到 255 后未回绕到 0 (实际值: %0d)\n", count);
    end

    // 测试5: 验证复位再次生效
    $fwrite(fd, "\n测试5: 验证复位再次生效\n");
    $fwrite(fd, "---------------------------\n");
    rst = 1;
    #10;
    if (count === 0) begin
        $fwrite(fd, "PASS: 再次复位后 count = 0\n");
    end else begin
        $fwrite(fd, "FAIL: 再次复位后 count != 0 (实际值: %0d)\n", count);
    end

    // 结束测试
    $fwrite(fd, "\n测试完成，关闭日志文件。\n");
    $fclose(fd);
    $finish;
end

endmodule