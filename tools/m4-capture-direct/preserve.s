.text
.globl mw34_capture_preserved_call
.seh_proc mw34_capture_preserved_call
mw34_capture_preserved_call:
  subq $616, %rsp
  .seh_stackalloc 616
  .seh_endprologue
  fxsave64 32(%rsp)
  fnstenv 544(%rsp)
  pushfq
  popq %r10
  movq %r10, 576(%rsp)
  movl $0x1f80, 584(%rsp)
  fninit
  ldmxcsr 584(%rsp)
  cld
  movq %rcx, %rax
  movq %rdx, %rcx
  callq *%rax
  fxrstor64 32(%rsp)
  fldenv 544(%rsp)
  pushq 576(%rsp)
  popfq
  leaq 616(%rsp), %rsp
  retq
.seh_endproc
