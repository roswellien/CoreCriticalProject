.intel_syntax noprefix
.text
.globl _fixture_fistp32
_fixture_fistp32:
    fld qword ptr [ecx]
    fistp dword ptr [edx]
    ret
