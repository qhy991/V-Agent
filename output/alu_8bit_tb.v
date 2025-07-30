module alu_8bit_tb();

    // Inputs
    reg [7:0] a;
    reg [7:0] b;
    reg [2:0] op;

    // Outputs
    wire [7:0] result;
    wire zero_flag;
    wire overflow_flag;

    // Instantiate the Unit Under Test (UUT)
    alu_8bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero_flag(zero_flag),
        .overflow_flag(overflow_flag)
    );

    initial begin
        // Initialize Inputs
        a = 8'h00;
        b = 8'h00;
        op = 3'b000;

        // Wait 10 ns for global reset to finish
        #10;

        // Test ADD operation
        a = 8'hFF;
        b = 8'h01;
        op = 3'b000;
        #10;

        // Test SUB operation
        a = 8'hFF;
        b = 8'h01;
        op = 3'b001;
        #10;

        // Test AND operation
        a = 8'hFF;
        b = 8'h0F;
        op = 3'b010;
        #10;

        // Test OR operation
        a = 8'hFF;
        b = 8'h0F;
        op = 3'b011;
        #10;

        // Test XOR operation
        a = 8'hFF;
        b = 8'h0F;
        op = 3'b100;
        #10;

        // Test default operation
        a = 8'hFF;
        b = 8'h0F;
        op = 3'b111;
        #10;

        // Finish simulation
        $finish;
    end

endmodule