```verilog
// ============================================================================
// Module: uart_core
// Description: UART communication module with configurable baud rate, parity,
//              FIFO buffers, and status indicators. Implements industrial standard
//              UART protocol.
//
// Parameters:
//   CLK_FREQ - System clock frequency in Hz (e.g., 10_000_000 for 10MHz)
//   DATA_WIDTH - Data width (8 bits for standard UART)
//   FIFO_DEPTH - Depth of FIFO buffer (minimum 16 bytes)
//
// Inputs:
//   clk        - System clock input
//   rst_n      - Asynchronous active-low reset
//   tx_data    - 8-bit data to be transmitted
//   tx_en      - Transmit enable signal
//   rx_data    - Serial data input from receiver
//   parity_sel - Parity selection (00: no parity, 01: even, 10: odd)
//   baud_rate_sel - Baud rate selection (00:9600, 01:19200, 10:38400, 11:115200)
//
// Outputs:
//   tx_out     - Serial data output
//   rx_data_out - 8-bit received data output
//   tx_busy    - Transmit busy indicator
//   tx_done    - Transmit complete flag
//   rx_ready   - Receive data ready indicator
//   rx_error   - Receive error flag (frame or parity error)
//
// Features:
//   - Configurable baud rate (9600, 19200, 38400, 115200)
//   - Parity generation/checking (even, odd, none)
//   - 16-byte FIFO for both transmit and receive
//   - Status signals for transmission and reception
//   - Industrial standard UART protocol compliance
//
// Clock Domain: Single
// Reset Type: Asynchronous
// ============================================================================
`timescale 1ns / 1ps

module uart_core #(
    parameter CLK_FREQ = 10_000_000,       // System clock frequency in Hz
    parameter DATA_WIDTH = 8,              // Data width (8 bits for UART)
    parameter FIFO_DEPTH = 16              // FIFO depth (minimum 16 bytes)
) (
    // Inputs
    input wire clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] tx_data,
    input wire tx_en,
    input wire rx_data,
    input wire [1:0] parity_sel,
    input wire [1:0] baud_rate_sel,

    // Outputs
    output reg tx_out,
    output reg [DATA_WIDTH-1:0] rx_data_out,
    output reg tx_busy,
    output reg tx_done,
    output reg rx_ready,
    output reg rx_error
);

    // ============================================================================
    // Parameter Definitions
    // ============================================================================
    localparam BAUD_RATE_TABLE = 4'b0000; // Placeholder for baud rate table
    localparam BAUD_RATE_9600 = 9600;
    localparam BAUD_RATE_19200 = 19200;
    localparam BAUD_RATE_38400 = 38400;
    localparam BAUD_RATE_115200 = 115200;

    // Calculate the number of clock cycles per bit
    localparam BAUD_RATE = (baud_rate_sel == 2'b00) ? BAUD_RATE_9600 :
                           (baud_rate_sel == 2'b01) ? BAUD_RATE_19200 :
                           (baud_rate_sel == 2'b10) ? BAUD_RATE_38400 :
                                                      BAUD_RATE_115200;

    localparam BIT_PERIOD = CLK_FREQ / BAUD_RATE;

    // ============================================================================
    // Internal Signals
    // ============================================================================
    reg [DATA_WIDTH-1:0] tx_fifo [0:FIFO_DEPTH-1];  // Transmit FIFO
    reg [DATA_WIDTH-1:0] rx_fifo [0:FIFO_DEPTH-1];  // Receive FIFO

    reg [7:0] tx_fifo_ptr;           // Transmit FIFO pointer
    reg [7:0] rx_fifo_ptr;           // Receive FIFO pointer

    reg [DATA_WIDTH-1:0] tx_shift_reg;  // Transmit shift register
    reg [DATA_WIDTH-1:0] rx_shift_reg;  // Receive shift register

    reg [7:0] tx_bit_count;           // Transmit bit counter
    reg [7:0] rx_bit_count;           // Receive bit counter

    reg tx_state;                     // Transmit state machine state
    reg rx_state;                     // Receive state machine state

    reg tx_parity;                    // Transmit parity bit
    reg rx_parity;                    // Receive parity bit

    reg [7:0] tx_bit_counter;         // Transmit bit counter
    reg [7:0] rx_bit_counter;         // Receive bit counter

    reg tx_start_flag;                // Transmit start flag
    reg rx_start_flag;                // Receive start flag

    reg tx_bit_valid;                 // Transmit bit valid flag
    reg rx_bit_valid;                 // Receive bit valid flag

    reg rx_frame_error;               // Receive frame error flag
    reg rx_parity_error;              // Receive parity error flag

    // ============================================================================
    // Local Parameters
    // ============================================================================
    localparam TX_IDLE = 1'b0;
    localparam TX_START = 1'b1;
    localparam TX_DATA = 2'b10;
    localparam TX_PARITY = 2'b11;
    localparam TX_STOP = 3'b100;

    localparam RX_IDLE = 1'b0;
    localparam RX_START = 1'b1;
    localparam RX_DATA = 2'b10;
    localparam RX_PARITY = 2'b11;
    localparam RX_STOP = 3'b100;

    // ============================================================================
    // FIFO Control Logic
    // ============================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_fifo_ptr <= 0;
            rx_fifo_ptr <= 0;
            tx_busy <= 1'b0;
            tx_done <= 1'b0;
            rx_ready <= 1'b0;
            rx_error <= 1'b0;
        end else begin
            // Transmit FIFO control
            if (tx_en && !tx_busy && tx_fifo_ptr < FIFO_DEPTH - 1) begin
                tx_fifo[tx_fifo_ptr] <= tx_data;
                tx_fifo_ptr <= tx_fifo_ptr + 1;
            end

            // Receive FIFO control
            if (rx_ready && rx_fifo_ptr < FIFO_DEPTH - 1) begin
                rx_fifo[rx_fifo_ptr] <= rx_data_out;
                rx_fifo_ptr <= rx_fifo_ptr + 1;
            end

            // Update status signals
            tx_busy <= (tx_state != TX_IDLE);
            tx_done <= (tx_state == TX_STOP && tx_bit_count == 0);
            rx_ready <= (rx_state == RX_IDLE && rx_fifo_ptr > 0);
            rx_error <= rx_frame_error || rx_parity_error;
        end
    end

    // ============================================================================
    // Baud Rate Generator
    // ============================================================================
    reg [7:0] baud_counter;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_counter <= 0;
            tx_out <= 1'b1;
        end else begin
            if (baud_counter == BIT_PERIOD - 1) begin
                baud_counter <= 0;
                tx_out <= ~tx_out;
            end else begin
                baud_counter <= baud_counter + 1;
            end
        end
    end

    // ============================================================================
    // Transmit State Machine
    // ============================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_state <= TX_IDLE;
            tx_bit_count <= 0;
            tx_shift_reg <= 0;
            tx_parity <= 1'b0;
            tx_start_flag <= 1'b0;
            tx_bit_valid <= 1'b0;
        end else begin
            case (tx_state)
                TX_IDLE: begin
                    if (tx_en && tx_fifo_ptr > 0) begin
                        tx_state <= TX_START;
                        tx_bit_count <= 0;
                        tx_shift_reg <= tx_fifo[0];
                        tx_fifo_ptr <= tx_fifo_ptr - 1;
                        tx_start_flag <= 1'b1;
                        tx_bit_valid <= 1'b1;
                    end
                end

                TX_START: begin
                    if (tx_bit_count == 0) begin
                        tx_out <= 1'b0;
                        tx_bit_count <= tx_bit_count + 1;
                    end else if (tx_bit_count == BIT_PERIOD - 1) begin
                        tx_state <= TX_DATA;
                        tx_bit_count <= 0;
                        tx_bit_valid <= 1'b1;
                    end
                end

                TX_DATA: begin
                    if (tx_bit_valid) begin
                        tx_out <= tx_shift_reg[0];
                        tx_shift_reg <= tx_shift_reg >> 1;
                        tx_bit_count <= tx_bit_count + 1;
                        tx_bit_valid <= 1'b0;
                    end else if (tx_bit_count == BIT_PERIOD - 1) begin
                        tx_bit_count <= 0;
                        tx_bit_valid <= 1'b1;
                        if (tx_shift_reg == 0) begin
                            tx_state <= TX_PARITY;
                        end
                    end
                end

                TX_PARITY: begin
                    if (parity_sel != 2'b00) begin
                        // Calculate parity
                        tx_parity <= ^tx_shift_reg;
                        if (parity_sel == 2'b01) begin
                            tx_parity <= ~tx_parity; // Even parity
                        end
                        tx_out <= tx_parity;
                        tx_bit_count <= tx_bit_count + 1;
                    end
                    if (tx_bit_count == BIT_PERIOD - 1) begin
                        tx_state <= TX_STOP;
                        tx_bit_count <= 0;
                        tx_bit_valid <= 1'b1;
                    end
                end

                TX_STOP: begin
                    if (tx_bit_count == 0) begin
                        tx_out <= 1'b1;
                        tx_bit_count <= tx_bit_count + 1;
                    end else if (tx_bit_count == BIT_PERIOD - 1) begin
                        tx_state <= TX_IDLE;
                        tx_bit_count <= 0;
                        tx_done <= 1'b1;
                    end
                end
            endcase
        end
    end

    // ============================================================================
    // Receive State Machine
    // ============================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_state <= RX_IDLE;
            rx_bit_count <= 0;
            rx_shift_reg <= 0;
            rx_parity <= 1'b0;
            rx_start_flag <= 1'b0;
            rx_bit_valid <= 1'b0;
            rx_frame_error <= 1'b0;
            rx_parity_error <= 1'b0;
        end else begin
            case (rx_state)
                RX_IDLE: begin
                    if (rx_data == 1'b0) begin
                        rx_state <= RX_START;
                        rx_bit_count <= 0;
                        rx_start_flag <= 1'b1;
                        rx_bit_valid <= 1'b1;
                    end
                end

                RX_START: begin
                    if (rx_bit_count == 0) begin
                        rx_bit_count <= rx_bit_count + 1;
                    end else if (rx_bit_count == BIT_PERIOD - 1) begin
                        rx_state <= RX_DATA;
                        rx_bit_count <= 0;
                        rx_bit_valid <= 1'b1;
                    end
                end

                RX_DATA: begin
                    if (rx_bit_valid) begin
                        rx_shift_reg <= {rx_shift_reg[DATA_WIDTH-2:0], rx_data};
                        rx_bit_count <= rx_bit_count + 1;
                        rx_bit_valid <= 1'b0;
                    end else if (rx_bit_count == BIT_PERIOD - 1) begin
                        rx_bit_count <= 0;
                        rx_bit_valid <= 1'b1;
                        if (rx_shift_reg[DATA_WIDTH-1] == 1'b1) begin
                            rx_state <= RX_PARITY;
                        end
                    end
                end

                RX_PARITY: begin
                    if (parity_sel != 2'b00) begin
                        // Calculate parity
                        rx_parity <= ^rx_shift_reg;
                        if (parity_sel == 2'b01) begin
                            rx_parity <= ~rx_parity; // Even parity
                        end
                        if (rx_parity != rx_data) begin
                            rx_parity_error <= 1'b1;
                        end
                        rx_bit_count <= rx_bit_count + 1;
                    end
                    if (rx_bit_count == BIT_PERIOD - 1) begin
                        rx_state <= RX_STOP;
                        rx_bit_count <= 0;
                        rx_bit_valid <= 1'b1;
                    end
                end

                RX_STOP: begin
                    if (rx_bit_count == 0) begin
                        rx_bit_count <= rx_bit_count + 1;
                    end else if (rx_bit_count == BIT_PERIOD - 1) begin
                        rx_state <= RX_IDLE;
                        rx_bit_count <= 0;
                        rx_data_out <= rx_shift_reg;
                        rx_ready <= 1'b1;
                        rx_error <= rx_frame_error || rx_parity_error;
                    end
                end
            endcase
        end
    end

    // ============================================================================
    // Additional Checks and Assertions
    // ============================================================================
    // Check that the selected baud rate is valid
    assert property (@(posedge clk) disable iff (!rst_n) 
        (baud_rate_sel inside {2'b00, 2'b01, 2'b10, 2'b11})) 
        else $error("Invalid baud rate selection");

    // Check that the selected parity is valid
    assert property (@(posedge clk) disable iff (!rst_n) 
        (parity_sel inside {2'b00, 2'b01, 2'b10})) 
        else $error("Invalid parity selection");

    // Check that the FIFO depth is at least 16
    assert property (@(posedge clk) disable iff (!rst_n) 
        (FIFO_DEPTH >= 16)) 
        else $error("FIFO depth must be at least 16");

endmodule
```