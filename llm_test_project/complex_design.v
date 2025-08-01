
module complex_processor (
    input wire clk,
    input wire reset,
    input wire [31:0] instruction_input,
    input wire [31:0] data_input,
    output reg [31:0] result_output,
    output reg operation_complete,
    output reg error_flag
);

// 复杂的状态机
reg [3:0] state;
reg [31:0] accumulator;
reg [31:0] memory [0:255];

localparam IDLE = 4'b0000;
localparam FETCH = 4'b0001;
localparam DECODE = 4'b0010;
localparam EXECUTE = 4'b0011;
localparam STORE = 4'b0100;

always @(posedge clk or posedge reset) begin
    if (reset) begin
        state <= IDLE;
        accumulator <= 32'b0;
        result_output <= 32'b0;
        operation_complete <= 1'b0;
        error_flag <= 1'b0;
    end else begin
        case (state)
            IDLE: begin
                if (instruction_input != 32'b0) begin
                    state <= FETCH;
                end
            end
            FETCH: state <= DECODE;
            DECODE: begin
                case (instruction_input[31:28])
                    4'b0001: state <= EXECUTE; // ADD
                    4'b0010: state <= EXECUTE; // SUB
                    4'b0011: state <= EXECUTE; // MUL
                    default: begin
                        error_flag <= 1'b1;
                        state <= IDLE;
                    end
                endcase
            end
            EXECUTE: begin
                case (instruction_input[31:28])
                    4'b0001: accumulator <= accumulator + data_input;
                    4'b0010: accumulator <= accumulator - data_input;
                    4'b0011: accumulator <= accumulator * data_input;
                endcase
                state <= STORE;
            end
            STORE: begin
                result_output <= accumulator;
                operation_complete <= 1'b1;
                state <= IDLE;
            end
            default: state <= IDLE;
        endcase
    end
end

endmodule
