#!/bin/bash
# Generated build script for simulation
# Simulator: iverilog

set -e  # Exit on any error

VERILOG_FILES="simple_8bit_adder.v full_adder.v"
TESTBENCH_FILES="simple_8bit_adder_tb.v"
TARGET="simulation"
VCD_FILE="$simulation.vcd"

# Function to compile
compile() {
    echo "Compiling design..."
    iverilog -o $TARGET $VERILOG_FILES $TESTBENCH_FILES
    echo "Compilation completed successfully"
}

# Function to simulate
simulate() {
    echo "Running simulation..."
    ./$TARGET
    echo "Simulation completed"
}

# Function to clean
clean() {
    echo "Cleaning generated files..."
    rm -f $TARGET $VCD_FILE *.vvp
    echo "Clean completed"
}

# Main execution
case "$1" in
    compile)
        compile
        ;;
    simulate)
        simulate
        ;;
    all)
        compile
        simulate
        ;;
    clean)
        clean
        ;;
    *)
        echo "Usage: $0 {compile|simulate|all|clean}"
        echo "  compile  - Compile the design"
        echo "  simulate - Run simulation"
        echo "  all      - Compile and simulate"
        echo "  clean    - Clean generated files"
        exit 1
        ;;
esac
