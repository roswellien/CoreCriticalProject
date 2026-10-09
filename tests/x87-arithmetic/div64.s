.intel_syntax noprefix
.text
.globl _fixture_div64
_fixture_div64:
    fld qword ptr [ecx]
    fdiv qword ptr [ecx+8]
    fstp qword ptr [edx]
    ret
