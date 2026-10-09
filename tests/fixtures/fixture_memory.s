.intel_syntax noprefix
.text
.globl _fixture_memory
_fixture_memory:
    mov eax, dword ptr [esp+4]
    mov ecx, dword ptr [esp+8]
    add ecx, dword ptr [eax]
    mov dword ptr [eax], ecx
    mov edx, dword ptr [eax+4]
    mov dword ptr [eax+8], edx
    mov eax, ecx
    ret 8
