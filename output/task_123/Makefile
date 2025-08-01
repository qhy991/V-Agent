all: compile simulate

compile:
	iverilog -o counter_sim output/task_123/counter.v output/task_123/counter_tb.v

simulate:
	vvp counter_sim

clean:
	rm -f counter_sim *.vcd