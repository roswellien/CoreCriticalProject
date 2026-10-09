.text
.globl own_nmx_boundary
.def own_nmx_boundary; .scl 2; .type 32; .endef
.seh_proc own_nmx_boundary
own_nmx_boundary:
  pushq %rbx
  .seh_pushreg %rbx
  pushq %rbp
  .seh_pushreg %rbp
  pushq %rsi
  .seh_pushreg %rsi
  pushq %rdi
  .seh_pushreg %rdi
  pushq %r12
  .seh_pushreg %r12
  pushq %r13
  .seh_pushreg %r13
  pushq %r14
  .seh_pushreg %r14
  pushq %r15
  .seh_pushreg %r15
  subq $616,%rsp
  .seh_stackalloc 616
  fxsave64 32(%rsp)
  .seh_savexmm %xmm6,288
  .seh_savexmm %xmm7,304
  .seh_savexmm %xmm8,320
  .seh_savexmm %xmm9,336
  .seh_savexmm %xmm10,352
  .seh_savexmm %xmm11,368
  .seh_savexmm %xmm12,384
  .seh_savexmm %xmm13,400
  .seh_savexmm %xmm14,416
  .seh_savexmm %xmm15,432
  .seh_endprologue
  fnstenv 544(%rsp)
  movq %rcx,%rsi
  movq %rdx,%rbx
  movq %r8,%rdi
  movq %r9,%rbp
  movabsq $0x1122334455667788,%r12
  movabsq $0x2233445566778899,%r13
  movabsq $0x33445566778899aa,%r14
  movabsq $0x445566778899aabb,%r15
  fninit
  fldcw 0(%rbp)
  ldmxcsr 24(%rbp)
  fldl own_nmx_a(%rip)
  fldl own_nmx_b(%rip)
  fxsave64 0(%rbx)
  fnstenv 512(%rbx)
  # Explicit authored occupied input, installed then observed on hardware.
  movw $0x3a20,2(%rbx)
  movb $0x81,4(%rbx)
  movl $0xffff3a20,516(%rbx)
  movl $0xffff3ffc,520(%rbx)
  movl $0x33445566,524(%rbx)
  movl $0x01230023,528(%rbx)
  movl $0x99aabbcc,532(%rbx)
  movl $0xffff002b,536(%rbx)
  fxrstor64 0(%rbx)
  fldenv 512(%rbx)
  movdqu 256(%rbp),%xmm6
  movdqu 272(%rbp),%xmm7
  movdqu 288(%rbp),%xmm8
  movdqu 304(%rbp),%xmm9
  movdqu 320(%rbp),%xmm10
  movdqu 336(%rbp),%xmm11
  movdqu 352(%rbp),%xmm12
  movdqu 368(%rbp),%xmm13
  movdqu 384(%rbp),%xmm14
  movdqu 400(%rbp),%xmm15
  fxsave64 0(%rbx)
  fnstenv 512(%rbx)
  fldenv 512(%rbx)
  movq %rbx,544(%rbx)
  movq %rbp,552(%rbx)
  movq %rsi,560(%rbx)
  movq %rdi,568(%rbx)
  movq %r12,576(%rbx)
  movq %r13,584(%rbx)
  movq %r14,592(%rbx)
  movq %r15,600(%rbx)
  movq %rsi,%rcx
  call own_nmx_invoke
  movl %eax,580(%rsp)
  # The after snapshot precedes any harness restoration.
  fxsave64 0(%rdi)
  fnstenv 512(%rdi)
  movq %rbx,544(%rdi)
  movq %rbp,552(%rdi)
  movq %rsi,560(%rdi)
  movq %rdi,568(%rdi)
  movq %r12,576(%rdi)
  movq %r13,584(%rdi)
  movq %r14,592(%rdi)
  movq %r15,600(%rdi)
  fxrstor64 32(%rsp)
  fldenv 544(%rsp)
  movl 580(%rsp),%eax
  addq $616,%rsp
  popq %r15
  popq %r14
  popq %r13
  popq %r12
  popq %rdi
  popq %rsi
  popq %rbp
  popq %rbx
  retq
.seh_endproc
.section .rdata,"dr"
.p2align 3
own_nmx_a: .double 1.25
own_nmx_b: .double 42.5
