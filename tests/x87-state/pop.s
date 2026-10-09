.intel_syntax noprefix
.text
.globl entry
entry:
  fstp tbyte ptr [edx]
  ret
