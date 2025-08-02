module task_tb;

    reg [7:0] a;
    reg [7:0] b;
    reg cin;
    wire [7:0] sum;
    wire cout;

    task test_case;
        input [7:0] a_val;
        input [7:0] b_val;
        input cin_val;
        input [7:0] expected_sum;
        input expected_cout;

        begin
            a = a_val;
            b = b_val;
            cin = cin_val;
            #10;
            $display("Test case: a=0x%h, b=0x%h, cin=%b => sum=0x%h, cout=%b", a, b, cin, sum, cout);
            if ({cout, sum} !== {expected_cout, expected_sum}) begin
                $display("Error: Expected {cout, sum} = {0x%h, 0x%h}, got {0x%h, 0x%h}", expected_cout, expected_sum, cout, sum);
            end
        end
    endtask

    initial begin
        // 测试用例1: 0 + 0 + 0 = 0, no carry
        test_case(8'h00, 8'h00, 1'b0, 8'h00, 1'b0);

        // 测试用例2: 0xFF + 0x01 + 0 = 0x00, carry=1
        test_case(8'hFF, 8'h01, 1'b0, 8'h00, 1'b1);

        // 测试用例3: 0x7F + 0x80 + 0 = 0xFF, no carry
        test_case(8'h7F, 8'h80, 1'b0, 8'hFF, 1'b0);

        // 测试用例4: 0x00 + 0x00 + 1 = 0x01, no carry
        test_case(8'h00, 8'h00, 1'b1, 8'h01, 1'b0);

        // 测试用例5: 0x00 + 0xFF + 1 = 0x00, carry=1
        test_case(8'h00, 8'hFF, 1'b1, 8'h00, 1'b1);

        // 测试用例6: 0x00 + 0x00 + 0 = 0x00, no carry
        test_case(8'h00, 8'h00, 1'b0, 8'h00, 1'b0);

        // 测试用例7: 0x00 + 0x01 + 0 = 0x01, no carry
        test_case(8'h00, 8'h01, 1'b0, 8'h01, 1'b0);

        // 测试用例8: 0x00 + 0x01 + 1 = 0x02, no carry
        test_case(8'h00, 8'h01, 1'b1, 8'h02, 1'b0);

        // 测试用例9: 0x00 + 0x00 + 1 = 0x01, no carry
        test_case(8'h00, 8'h00, 1'b1, 8'h01, 1'b0);

        // 测试用例10: 0x00 + 0x00 + 0 = 0x00, no carry
        test_case(8'h00, 8'h00, 1'b0, 8'h00, 1'b0);

        $finish;
    end

endmodule