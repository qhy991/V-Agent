// Simple assembly program to sort an array

.section .text
.global _start
_start:
    la t0, array    // Load address of array
    li t1, 0        // Index counter
    li t2, 5        // Number of elements in array

sort_loop:
    lw t3, 0(t0)    // Load first element
    lw t4, 4(t0)    // Load second element
    slt t5, t3, t4  // Check if first element is less than second
    beq t5, 1, swap // If not, swap them
    j continue

swap:
    sw t4, 0(t0)    // Store second element at first position
    sw t3, 4(t0)    // Store first element at second position

continue:
    addi t0, t0, 4  // Move to next pair of elements
    addi t1, t1, 1  // Increment index counter
    blt t1, t2, sort_loop // Continue loop if index < 5

    // End of program
    j _start

.section .data
    .align 2
    array: .word 5, 3, 8, 1, 4  // Array to sort
    .space 1024   // Reserve space for data memory