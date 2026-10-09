.intel_syntax noprefix
.text
.globl _fixture_shift
_fixture_shift:
    mov eax, dword ptr [esp+4]
    shl eax, 5
    sub eax, dword ptr [esp+8]
    ret
