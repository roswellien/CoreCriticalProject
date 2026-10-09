.intel_syntax noprefix
.text
.globl _fixture_mul64
_fixture_mul64:
    fld qword ptr [ecx]
    fmul qword ptr [ecx+8]
    fstp qword ptr [edx]
    ret
