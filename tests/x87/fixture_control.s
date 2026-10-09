.intel_syntax noprefix
.text
.globl _fixture_control
_fixture_control:
    fnstcw word ptr [ecx]
    ret
