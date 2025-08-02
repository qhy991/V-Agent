module tb_counter_8bit;

    reg clk;
    reg rst_n;
    reg enable;
    reg up_down;
    wire [7:0] count;
    wire overflow;

    // 实例化被测模块
    counter_8bit uut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .up_down(up_down),
        .count(count),
        .overflow(overflow)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // 测试过程
    initial begin
        // 初始化信号
        rst_n = 0;
        enable = 0;
        up_down = 0;
        #10;
        rst_n = 1;
        #10;

        // 基本功能测试
        enable = 1;
        up_down = 1;
        #100;
        enable = 0;
        #10;

        // 方向控制测试
        up_down = 0;
        #100;
        up_down = 1;
        #100;

        // 边界条件测试
        enable = 1;
        up_down = 1;
        #100;
        enable = 0;
        #10;

        $finish;
    end

endmodule