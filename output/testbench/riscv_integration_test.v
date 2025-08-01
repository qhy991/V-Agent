// RISC-V CPU Integration Test Module
// This module combines all test components for comprehensive verification
module riscv_integration_test (
    input clk,
    input rst_n,
    input test_mode,
    output reg test_result,
    output reg error_flag,
    output reg [31:0] performance_metrics
);

    // Instantiate testbench components
    riscv_testbench tb (
        .clk(clk),
        .rst_n(rst_n),
        .start_test(test_mode),
        .test_result(test_result),
        .error_flag(error_flag)
    );

    // Instantiate performance monitor
    riscv_performance_monitor pm (
        .clk(clk),
        .rst_n(rst_n),
        .instruction_count(32'h00000000),
        .resource_usage(32'h00000000),
        .execution_cycles(performance_metrics[31:16]),
        .resource_utilization(performance_metrics[15:8]),
        .critical_path_delay(performance_metrics[7:0])
    );

endmodule