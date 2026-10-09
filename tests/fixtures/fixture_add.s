# Project-authored, fixed instruction sequence; no game bytes.
.intel_syntax noprefix
.text
.globl _fixture_add
_fixture_add:
    mov eax, dword ptr [esp + 4]
    add eax, dword ptr [esp + 8]
    ret
