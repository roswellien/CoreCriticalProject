.intel_syntax noprefix
.text
.globl _fixture_add_sub
_fixture_add_sub:
    fld qword ptr [ecx]
    fadd qword ptr [ecx + 8]
    fsub qword ptr [ecx]
    fstp qword ptr [edx]
    ret
