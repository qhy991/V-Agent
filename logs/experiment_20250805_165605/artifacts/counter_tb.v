module counter_tb ();

reg clk;
reg rst;
reg en;
wire [7:0] count;

// 被测模块实例化
counter_with_comments uut (
    .clk(clk),
    .reset(rst),
    .enable(en),
    .count(count)
);

// 时钟生成
always #5 clk = ~clk; // 10ns周期时钟

initial begin
    // 初始化信号
    clk = 0;
    rst = 0;
    en = 0;
    
    $display("=== 计数器模块测试开始 ===");
    
    // 测试1: 复位功能测试
    $display("测试1: 复位功能");
    rst = 1;
    #20;
    rst = 0;
    if (count === 8'h00) $display("复位测试通过");
    else $display("复位测试失败");
    
    // 测试2: 使能信号控制
    $display("测试2: 使能信号控制");
    en = 0;
    #100; // 等待多个时钟周期
    if (count === 8'h00) $display("使能控制测试通过");
    else $display("使能控制测试失败");
    
    // 测试3: 正常计数功能
    $display("测试3: 正常计数功能");
    en = 1;
    #260; // 等待计数到3
    if (count === 8'h03) $display("正常计数测试通过");
    else $display("正常计数测试失败");
    
    // 测试4: 边界条件测试
    $display("测试4: 边界条件测试");
    // 强制设置计数器到255
    uut.count = 8'hFF;
    #10;
    if (count === 8'hFF) $display("最大值测试通过");
    else $display("最大值测试失败");
    
    $display("=== 计数器模块测试结束 ===");
    $finish;
end

endmodule