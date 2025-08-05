# Generated Makefile for simulation
# Simulator: iverilog

VERILOG_FILES = counter.v
TESTBENCH_FILES = tb_counter.v
ALL_FILES = $(VERILOG_FILES) $(TESTBENCH_FILES)

TARGET = simulation
VCD_FILE = $(TARGET).vcd

# Default target
all: compile simulate

# Compile the design
compile: $(TARGET)

$(TARGET): $(ALL_FILES)
	iverilog -o $(TARGET) $(ALL_FILES)

# Run simulation
simulate: $(TARGET)
	./$(TARGET)

# View waveforms (if GTKWave is available)
waves: $(VCD_FILE)
	gtkwave $(VCD_FILE) &

# Clean generated files
clean:
	rm -f $(TARGET) $(VCD_FILE) *.vvp

# Lint check
lint:
	verilator --lint-only $(VERILOG_FILES)

.PHONY: all compile simulate waves clean lint
