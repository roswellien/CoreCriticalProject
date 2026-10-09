.intel_syntax noprefix
.text
.globl _fixture_spill64
_fixture_spill64:
    fld qword ptr [ecx]
    fadd qword ptr [ecx + 8]
    fstp qword ptr [edx + 8]
    fld qword ptr [edx + 8]
    fsub qword ptr [ecx]
    fstp qword ptr [edx]
    ret
