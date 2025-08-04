module uut (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(data_in),
        .data_out(data_out)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 10ns周期时钟
    end

    // 测试序列
    initial begin
        // 初始化
        rst_n = 0;
        data_in = 8'h0;
        #10;
        
        // 复位
        rst_n = 1;
        #10;
        
        // 测试数据输入
        data_in = 8'hAA;
        #10;
        
        data_in = 8'h55;
        #10;
        
        data_in = 8'hFF;
        #10;
        
        data_in = 8'h00;
        #10;
        
        // 结束仿真
        $finish;
    end

    // 显示波形
    initial begin
        $dumpfile("testbench_design_module.vcd");
        $dumpvars(0, testbench_design_module);
    end

endmodule