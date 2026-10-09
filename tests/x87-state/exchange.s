.intel_syntax noprefix
.text
.globl entry
entry:
  fxch st(1)
  ret
