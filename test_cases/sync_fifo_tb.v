`timescale 1ns / 1ps

//========================================================================
// 同步FIFO测试台 - 严格按照接口规范设计
//========================================================================
module sync_fifo_tb;

    // 测试台参数
    parameter CLK_PERIOD = 10;  // 10ns时钟周期
    parameter DATA_WIDTH = 8;
    parameter FIFO_DEPTH = 16;
    parameter ADDR_WIDTH = 4;   // log2(16) = 4
    
    // 信号声明 - 严格匹配接口规范
    reg                    clk;
    reg                    rst_n;        // 注意：使用rst_n（低电平复位）
    reg                    wr_en;
    reg                    rd_en;
    reg  [DATA_WIDTH-1:0]  wr_data;
    wire [DATA_WIDTH-1:0]  rd_data;
    wire                   full;
    wire                   empty;
    wire [ADDR_WIDTH:0]    count;       // FIFO中数据个数
    
    // 被测模块实例化 - 接口名称必须完全匹配
    sync_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .FIFO_DEPTH(FIFO_DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) dut (
        .clk(clk),           // 时钟
        .rst_n(rst_n),       // 异步复位（低电平有效）- 关键接口
        .wr_en(wr_en),       // 写使能
        .rd_en(rd_en),       // 读使能
        .wr_data(wr_data),   // 写数据
        .rd_data(rd_data),   // 读数据
        .full(full),         // 满标志
        .empty(empty),       // 空标志
        .count(count)        // 计数
    );
    
    // 时钟生成
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end
    
    // 测试变量
    integer i;
    reg [DATA_WIDTH-1:0] test_data;
    reg [DATA_WIDTH-1:0] expected_data;
    integer error_count;
    
    // 主测试流程
    initial begin
        $display("=================================================================");
        $display("开始同步FIFO功能测试");
        $display("时间: %0t", $time);
        $display("=================================================================");
        
        // 初始化信号
        rst_n = 0;
        wr_en = 0;
        rd_en = 0;
        wr_data = 0;
        error_count = 0;
        
        // 复位测试
        $display("\n--- 测试用例1: 异步复位功能测试 ---");
        #(CLK_PERIOD * 2);
        if (empty !== 1'b1 || full !== 1'b0 || count !== 0) begin
            $display("❌ 复位测试失败: empty=%b, full=%b, count=%d", empty, full, count);
            error_count = error_count + 1;
        end else begin
            $display("✅ 复位测试通过: FIFO正确复位为空状态");
        end
        
        // 释放复位
        rst_n = 1;
        #(CLK_PERIOD);
        
        // 写入测试
        $display("\n--- 测试用例2: 写入功能测试 ---");
        for (i = 0; i < 8; i = i + 1) begin
            @(posedge clk);
            wr_en = 1;
            wr_data = 8'hA0 + i;  // 写入测试数据 A0, A1, A2...
            @(posedge clk);
            wr_en = 0;
            #1;  // 等待信号稳定
            $display("写入数据[%0d]: 0x%02X, count=%d, full=%b", i, wr_data, count, full);
        end
        
        // 检查写入后状态
        if (count !== 8) begin
            $display("❌ 写入测试失败: 期望count=8, 实际count=%d", count);
            error_count = error_count + 1;
        end else begin
            $display("✅ 写入测试通过: 成功写入8个数据");
        end
        
        // 读取测试
        $display("\n--- 测试用例3: 读取功能测试 ---");
        for (i = 0; i < 8; i = i + 1) begin
            expected_data = 8'hA0 + i;
            @(posedge clk);
            rd_en = 1;
            @(posedge clk);
            rd_en = 0;
            #1;  // 等待信号稳定
            $display("读取数据[%0d]: 0x%02X (期望: 0x%02X), count=%d, empty=%b", 
                    i, rd_data, expected_data, count, empty);
            
            if (rd_data !== expected_data) begin
                $display("❌ 数据不匹配: 读取=0x%02X, 期望=0x%02X", rd_data, expected_data);
                error_count = error_count + 1;
            end
        end
        
        // 检查读取后状态
        if (count !== 0 || empty !== 1'b1) begin
            $display("❌ 读取测试失败: 期望count=0且empty=1, 实际count=%d, empty=%b", count, empty);
            error_count = error_count + 1;
        end else begin
            $display("✅ 读取测试通过: FIFO正确变为空状态");
        end
        
        // 满状态测试
        $display("\n--- 测试用例4: 满状态测试 ---");
        for (i = 0; i < FIFO_DEPTH; i = i + 1) begin
            @(posedge clk);
            wr_en = 1;
            wr_data = 8'h10 + i;
            @(posedge clk);
            wr_en = 0;
            #1;
        end
        
        if (full !== 1'b1 || count !== FIFO_DEPTH) begin
            $display("❌ 满状态测试失败: 期望full=1且count=%d, 实际full=%b, count=%d", 
                    FIFO_DEPTH, full, count);
            error_count = error_count + 1;
        end else begin
            $display("✅ 满状态测试通过: FIFO正确检测满状态");
        end
        
        // 溢出保护测试
        $display("\n--- 测试用例5: 溢出保护测试 ---");
        @(posedge clk);
        wr_en = 1;
        wr_data = 8'hFF;  // 尝试在满状态下写入
        @(posedge clk);
        wr_en = 0;
        #1;
        
        if (count > FIFO_DEPTH) begin
            $display("❌ 溢出保护失败: count=%d 超过了FIFO深度", count);
            error_count = error_count + 1;
        end else begin
            $display("✅ 溢出保护测试通过: 满状态下写入被正确忽略");
        end
        
        // 同时读写测试
        $display("\n--- 测试用例6: 同时读写测试 ---");
        // 先清空FIFO
        while (!empty) begin
            @(posedge clk);
            rd_en = 1;
            @(posedge clk);
            rd_en = 0;
            #1;
        end
        
        // 同时进行读写操作
        for (i = 0; i < 5; i = i + 1) begin
            @(posedge clk);
            wr_en = 1;
            rd_en = (i > 0) ? 1 : 0;  // 第一次只写不读
            wr_data = 8'h20 + i;
            @(posedge clk);
            wr_en = 0;
            rd_en = 0;
            #1;
            $display("同时读写[%0d]: wr_data=0x%02X, rd_data=0x%02X, count=%d", 
                    i, wr_data, rd_data, count);
        end
        
        // 测试总结
        $display("\n=================================================================");
        if (error_count == 0) begin
            $display("🎉 所有测试通过! FIFO设计功能正确");
        end else begin
            $display("❌ 发现 %0d 个错误，需要修复设计", error_count);
        end
        $display("测试完成时间: %0t", $time);
        $display("=================================================================");
        
        // 生成波形文件
        $dumpfile("sync_fifo_tb.vcd");
        $dumpvars(0, sync_fifo_tb);
        
        #(CLK_PERIOD * 5);
        $finish;
    end
    
    // 监控重要信号变化
    always @(posedge clk) begin
        if (rst_n && (wr_en || rd_en)) begin
            $display("时间 %0t: wr_en=%b, rd_en=%b, wr_data=0x%02X, rd_data=0x%02X, count=%d, full=%b, empty=%b",
                    $time, wr_en, rd_en, wr_data, rd_data, count, full, empty);
        end
    end
    
    // 错误检测
    always @(posedge clk) begin
        if (rst_n) begin
            // 检查count的合理性
            if (count > FIFO_DEPTH) begin
                $display("❌ 错误: count=%d 超过FIFO深度 %d", count, FIFO_DEPTH);
            end
            
            // 检查full和empty的一致性
            if (full && empty) begin
                $display("❌ 错误: full和empty不能同时为1");
            end
            
            if (count == 0 && !empty) begin
                $display("❌ 错误: count=0时empty应该为1");
            end
            
            if (count == FIFO_DEPTH && !full) begin
                $display("❌ 错误: count=FIFO_DEPTH时full应该为1");
            end
        end
    end

endmodule