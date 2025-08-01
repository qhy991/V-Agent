// RISC-V assembly programs for testing
// Fibonacci sequence calculation
li x1, 10
li x2, 0
li x3, 1

loop:
add x4, x2, x3
sw x4, 0(x5)
add x2, x3, x4
add x3, x4, x2
subi x1, x1, 1
bnez x1, loop