// Simple assembly program to test loops and conditional branches

.section .text
.global _start
_start:
    li t0, 0        // Initialize counter
    li t1, 10       // Maximum value

loop:
    addi t0, t0, 1  // Increment counter
    blt t0, t1, loop // Continue loop if counter < 10

    // End of program
    j _start

.section .data
    .align 2
    .space 1024   // Reserve space for data memory