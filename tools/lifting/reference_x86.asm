; Capture must not write to guest memory or alter flags before observation.
.386
.model flat, C
option casemap:none

EXTERN mw_input:BYTE
EXTERN mw_output:BYTE
EXTERN mw_host_esp:DWORD
EXTERN mw_entry:DWORD
PUBLIC mw_enter_guest
PUBLIC mw_capture_guest

.code
mw_enter_guest PROC
    pushfd
    pushad
    mov mw_host_esp, esp
    push DWORD PTR mw_input[32]
    popfd
    mov eax, DWORD PTR mw_input[0]
    mov ecx, DWORD PTR mw_input[4]
    mov edx, DWORD PTR mw_input[8]
    mov ebx, DWORD PTR mw_input[12]
    mov ebp, DWORD PTR mw_input[20]
    mov esi, DWORD PTR mw_input[24]
    mov edi, DWORD PTR mw_input[28]
    mov esp, DWORD PTR mw_input[16]
    jmp DWORD PTR mw_entry
mw_enter_guest ENDP

mw_capture_guest PROC
    mov DWORD PTR mw_output[0], eax
    mov DWORD PTR mw_output[4], ecx
    mov DWORD PTR mw_output[8], edx
    mov DWORD PTR mw_output[12], ebx
    mov DWORD PTR mw_output[16], esp
    mov DWORD PTR mw_output[20], ebp
    mov DWORD PTR mw_output[24], esi
    mov DWORD PTR mw_output[28], edi
    mov esp, mw_host_esp
    pushfd
    pop DWORD PTR mw_output[32]
    mov DWORD PTR mw_output[36], 10000100h
    popad
    popfd
    ret
mw_capture_guest ENDP
END
