.text
.globl mfc_hardware_call
.seh_proc mfc_hardware_call
mfc_hardware_call:
  pushq %rbx
  .seh_pushreg %rbx
  subq $32, %rsp
  .seh_stackalloc 32
  .seh_endprologue
  movq %rdx, %rbx
  fxsave64 0(%rbx)
  fnstenv 512(%rbx)
  fldenv 512(%rbx)
  callq mfc_invoke_guarded
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
