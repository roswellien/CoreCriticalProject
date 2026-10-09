.intel_syntax noprefix
.text
.globl entry
entry:
  fld tbyte ptr [ecx]
  ret
