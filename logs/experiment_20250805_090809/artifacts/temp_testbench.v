`timescale 1ns/1ps

module tb_counter;
    // �ź�����
    reg clk;
    reg reset;
    reg enable;
    wire [3:0] count;

    // ʵ��������ģ��
    counter uut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .count(count)
    );

    // ʱ������: 10ns���� (5ns��, 5ns��)
    always #5 clk = ~clk;

    // ��ʼ������
    initial begin
        // �򿪲���ת������ѡ��
        $dumpfile("counter_wave.vcd");
        $dumpvars(0, tb_counter);

        // ��ʼ���ź�
        clk = 0;
        reset = 1;
        enable = 0;

        // ��λ����10��ʱ������
        repeat(10) @(posedge clk);
        reset = 0;

        // ���ü�����
        enable = 1;

        // �۲������Ϊ������20��ʱ������
        repeat(20) @(posedge clk);

        // ��֤���ռ���ֵ
        if (count == 4'd20) begin
            $display("[PASS] Test passed: count = %d as expected.", count);
        end else begin
            $display("[FAIL] Test failed: expected count = 20, got %d", count);
        end

        // ��������
        $finish;
    end
endmodule