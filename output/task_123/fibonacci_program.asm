// Simple assembly program to compute Fibonacci sequence

.section .text
.global _start
_start:
    li t0, 0      // Initialize first Fibonacci number
    li t1, 1      // Initialize second Fibonacci number
    li t2, 0      // Counter
    li t3, 10     // Number of Fibonacci numbers to compute

loop:
    add t4, t0, t1  // Compute next Fibonacci number
    mv t0, t1       // Update first number
    mv t1, t4       // Update second number
    addi t2, t2, 1  // Increment counter
    blt t2, t3, loop // Continue loop if counter < 10

    // End of program
    j _start

.section .data
    .align 2
    .space 1024   // Reserve space for data memory