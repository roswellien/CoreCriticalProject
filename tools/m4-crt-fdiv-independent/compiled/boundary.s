.text
.globl own_fd_boundary
.seh_proc own_fd_boundary
own_fd_boundary:
  pushq %rbx
  .seh_pushreg %rbx
  pushq %rbp
  .seh_pushreg %rbp
  pushq %rsi
  .seh_pushreg %rsi
  pushq %rdi
  .seh_pushreg %rdi
  subq $584, %rsp
  .seh_stackalloc 584
  fxsave64 32(%rsp)
  .seh_savexmm %xmm6, 288
  .seh_savexmm %xmm7, 304
  .seh_savexmm %xmm8, 320
  .seh_savexmm %xmm9, 336
  .seh_savexmm %xmm10, 352
  .seh_savexmm %xmm11, 368
  .seh_savexmm %xmm12, 384
  .seh_savexmm %xmm13, 400
  .seh_savexmm %xmm14, 416
  .seh_savexmm %xmm15, 432
  .seh_endprologue
  fnstenv 544(%rsp)
  fldenv 544(%rsp)
  movq %rcx, %rbx
  movq %rdx, %rsi
  movq %r8, %rdi
  fninit
  fldcw own_fd_cw(%rip)
  fldl own_fd_live_a(%rip)
  fldl own_fd_live_b(%rip)
  fld1
  fdivl own_fd_three(%rip)
  fstpl 576(%rsp)
  movdqu 256(%r9), %xmm6
  movdqu 272(%r9), %xmm7
  movdqu 288(%r9), %xmm8
  movdqu 304(%r9), %xmm9
  movdqu 320(%r9), %xmm10
  movdqu 336(%r9), %xmm11
  movdqu 352(%r9), %xmm12
  movdqu 368(%r9), %xmm13
  movdqu 384(%r9), %xmm14
  movdqu 400(%r9), %xmm15
  fxsave64 (%rsi)
  fnstenv 512(%rsi)
  fldenv 512(%rsi)
  movq %rbx, %rcx
  callq own_fd_initialize
  movl %eax, %ebp
  fxsave64 (%rdi)
  fnstenv 512(%rdi)
  fldenv 512(%rdi)
  fxrstor64 32(%rsp)
  fldenv 544(%rsp)
  movl %ebp, %eax
  addq $584, %rsp
  popq %rdi
  popq %rsi
  popq %rbp
  popq %rbx
  retq
.seh_endproc
.section .rdata,"dr"
.p2align 3
own_fd_live_a: .double 1.25
own_fd_live_b: .double 42.5
own_fd_three: .double 3.0
own_fd_cw: .short 0x0b7f
