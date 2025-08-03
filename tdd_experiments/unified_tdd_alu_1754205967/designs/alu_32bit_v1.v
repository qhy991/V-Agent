module alu_32bit #(
    parameter WIDTH = 32
) (
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input [3:0] op,
    output reg [WIDTH-1:0] result,
    output reg zero,
    output reg overflow
);

// Internal signals
reg [WIDTH-1:0] add_result;
reg [WIDTH-1:0] sub_result;
reg [WIDTH-1:0] and_result;
reg [WIDTH-1:0] or_result;
reg [WIDTH-1:0] xor_result;
reg [WIDTH-1:0] not_result;
reg [WIDTH-1:0] eq_result;
reg [WIDTH-1:0] lt_result;
reg [WIDTH-1:0] gt_result;

// Combinational logic for operations
always @(*) begin
    add_result = a + b;
    sub_result = a - b;
    and_result = a & b;
    or_result = a | b;
    xor_result = a ^ b;
    not_result = ~a;
    
    // Equality check (eq)
    eq_result = (a == b) ? {WIDTH{1'b1}} : {WIDTH{1'b0}};
    
    // Less than (lt): signed comparison
    lt_result = ($signed(a) < $signed(b)) ? {WIDTH{1'b1}} : {WIDTH{1'b0}};
    
    // Greater than (gt): signed comparison
    gt_result = ($signed(a) > $signed(b)) ? {WIDTH{1'b1}} : {WIDTH{1'b0}};
end

// Overflow detection for ADD and SUB
always @(*) begin
    if (op == 4'b0000) begin // ADD
        overflow = ($signed(a) > 0 && $signed(b) > 0 && $signed(add_result) < 0) ||
                   ($signed(a) < 0 && $signed(b) < 0 && $signed(add_result) > 0);
    end else if (op == 4'b0001) begin // SUB
        overflow = ($signed(a) > 0 && $signed(b) < 0 && $signed(sub_result) < 0) ||
                   ($signed(a) < 0 && $signed(b) > 0 && $signed(sub_result) > 0);
    end else begin
        overflow = 1'b0; // No overflow for other operations
    end
end

// Select result based on operation code
always @(*) begin
    case (op)
        4'b0000: result = add_result;
        4'b0001: result = sub_result;
        4'b0010: result = and_result;
        4'b0011: result = or_result;
        4'b0100: result = xor_result;
        4'b0101: result = not_result;
        4'b0110: result = eq_result;
        4'b0111: result = lt_result;
        4'b1000: result = gt_result;
        default: result = {WIDTH{1'b0}};
    endcase
end

// Zero flag: set when result is zero
always @(*) begin
    zero = (result == 0) ? 1'b1 : 1'b0;
end

// Synchronous reset and clocked behavior
always @(posedge clk or posedge rst) begin
    if (rst) begin
        result <= 32'd0;
        zero <= 1'b0;
        overflow <= 1'b0;
    end else begin
        // Update outputs on clock edge
        // Note: Since all logic is combinational, outputs are updated directly
        // The registers hold the current values
    end
end

endmodule