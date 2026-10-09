.intel_syntax noprefix
.text
.globl _fixture_branch
_fixture_branch:
    mov eax, dword ptr [esp+4]
    cmp eax, dword ptr [esp+8]
    jge .greater_equal
    mov eax, dword ptr [esp+8]
    mov cl, 0x11
    ret
.greater_equal:
    mov cx, 0x2233
    ret
