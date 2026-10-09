.text
.globl mw34_capture_test_boundary
.seh_proc mw34_capture_test_boundary
mw34_capture_test_boundary:
  pushq %rbx
  .seh_pushreg %rbx
  pushq %rsi
  .seh_pushreg %rsi
  pushq %rdi
  .seh_pushreg %rdi
  subq $192, %rsp
  .seh_stackalloc 192
  movdqu %xmm6, 32(%rsp)
  .seh_savexmm %xmm6, 32
  movdqu %xmm7, 48(%rsp)
  .seh_savexmm %xmm7, 48
  movdqu %xmm8, 64(%rsp)
  .seh_savexmm %xmm8, 64
  movdqu %xmm9, 80(%rsp)
  .seh_savexmm %xmm9, 80
  movdqu %xmm10, 96(%rsp)
  .seh_savexmm %xmm10, 96
  movdqu %xmm11, 112(%rsp)
  .seh_savexmm %xmm11, 112
  movdqu %xmm12, 128(%rsp)
  .seh_savexmm %xmm12, 128
  movdqu %xmm13, 144(%rsp)
  .seh_savexmm %xmm13, 144
  movdqu %xmm14, 160(%rsp)
  .seh_savexmm %xmm14, 160
  movdqu %xmm15, 176(%rsp)
  .seh_savexmm %xmm15, 176
  .seh_endprologue
  movq %rcx, %rbx
  movq %rdx, %rsi
  movq %r8, %rdi
  fxrstor64 (%r9)
  fldenv 512(%r9)
  fxsave64 (%rsi)
  fnstenv 512(%rsi)
  fldenv 512(%rsi)
  pushfq
  popq 544(%rsi)
  movq %rbx, %rcx
  callq mw34_capture_test_operation
  fxsave64 (%rdi)
  fnstenv 512(%rdi)
  fldenv 512(%rdi)
  pushfq
  popq 544(%rdi)
  cld
  movdqu 32(%rsp), %xmm6
  movdqu 48(%rsp), %xmm7
  movdqu 64(%rsp), %xmm8
  movdqu 80(%rsp), %xmm9
  movdqu 96(%rsp), %xmm10
  movdqu 112(%rsp), %xmm11
  movdqu 128(%rsp), %xmm12
  movdqu 144(%rsp), %xmm13
  movdqu 160(%rsp), %xmm14
  movdqu 176(%rsp), %xmm15
  addq $192, %rsp
  popq %rdi
  popq %rsi
  popq %rbx
  retq
.seh_endproc
