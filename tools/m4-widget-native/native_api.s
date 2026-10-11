.text
.globl mw34_widget_native_api
.seh_proc mw34_widget_native_api
mw34_widget_native_api:
  pushq %rbx
  .seh_pushreg %rbx
  pushq %rsi
  .seh_pushreg %rsi
  pushq %rdi
  .seh_pushreg %rdi
  subq $112, %rsp
  .seh_stackalloc 112
  .seh_endprologue
  movq %rcx, %rbx
  movq %rdx, %rsi
  movq %r8, %rdi
  movq 32(%rsi), %rax
  movq %rax, 32(%rsp)
  movq 40(%rsi), %rax
  movq %rax, 40(%rsp)
  movq 48(%rsi), %rax
  movq %rax, 48(%rsp)
  movq 56(%rsi), %rax
  movq %rax, 56(%rsp)
  movq 64(%rsi), %rax
  movq %rax, 64(%rsp)
  movq 72(%rsi), %rax
  movq %rax, 72(%rsp)
  movq 80(%rsi), %rax
  movq %rax, 80(%rsp)
  movq 88(%rsi), %rax
  movq %rax, 88(%rsp)
  movq 96(%rsi), %rax
  movq %rax, 96(%rsp)
  movq 104(%rsi), %rax
  movq %rax, 104(%rsp)
  movq 0(%rsi), %rcx
  movq 8(%rsi), %rdx
  movq 16(%rsi), %r8
  movq 24(%rsi), %r9
  movq %rax, 0(%rdi)
  movq %rcx, 8(%rdi)
  movq %rdx, 16(%rdi)
  pushfq
  popq 24(%rdi)
  fxsave64 32(%rdi)
  fnstenv 544(%rdi)
  fldenv 544(%rdi)
  callq *%rbx
  movq %rax, 576(%rdi)
  movq %rcx, 584(%rdi)
  movq %rdx, 592(%rdi)
  pushfq
  popq 600(%rdi)
  fxsave64 608(%rdi)
  fnstenv 1120(%rdi)
  fldenv 1120(%rdi)
  addq $112, %rsp
  popq %rdi
  popq %rsi
  popq %rbx
  retq
.seh_endproc

.globl mw34_widget_hardware_call
.seh_proc mw34_widget_hardware_call
mw34_widget_hardware_call:
  pushq %rbx
  .seh_pushreg %rbx
  subq $32, %rsp
  .seh_stackalloc 32
  .seh_endprologue
  movq %rdx, %rbx
  fxsave64 0(%rbx)
  fnstenv 512(%rbx)
  fldenv 512(%rbx)
  callq mw34_widget_invoke_guarded
  fxsave64 544(%rbx)
  fnstenv 1056(%rbx)
  fldenv 1056(%rbx)
  fxrstor64 0(%rbx)
  fldenv 512(%rbx)
  fxsave64 1088(%rbx)
  fnstenv 1600(%rbx)
  fldenv 1600(%rbx)
  addq $32, %rsp
  popq %rbx
  retq
.seh_endproc
