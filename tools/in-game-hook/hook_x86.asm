; Authored entry/capture bridges. No game instruction bytes are embedded here.
.686p
.xmm
.model flat, C
option casemap:none
EXTERN mw34_dispatch:PROC
EXTERN mw34_shadow_input:BYTE
EXTERN mw34_shadow_output:BYTE
EXTERN mw34_shadow_host_esp:DWORD
EXTERN mw34_shadow_entry:DWORD
EXTERN mw34_shadow_sentinel:DWORD
EXTERN mw34_hook_input:BYTE
EXTERN mw34_hook_output:BYTE
EXTERN mw34_hook_host_esp:DWORD
EXTERN mw34_hook_sentinel:DWORD
EXTERN mw34_hook_fp_input:BYTE
EXTERN mw34_hook_fp_output:BYTE
PUBLIC mw34_hook_entry
PUBLIC mw34_enter_shadow
PUBLIC mw34_capture_shadow
PUBLIC mw34_enter_hook_test
PUBLIC mw34_capture_hook_test
.code
mw34_hook_entry PROC
    pushfd
    pushad
    mov ebx, esp
    sub esp, 544
    and esp, -16
    fxsave [esp]
    mov esi, esp
    cld
    push ebx
    call mw34_dispatch
    add esp, 4
    fxrstor [esi]
    mov esp, ebx
    popad
    popfd
    ret 4
mw34_hook_entry ENDP
mw34_enter_shadow PROC
    pushfd
    pushad
    mov mw34_shadow_host_esp, esp
    push DWORD PTR mw34_shadow_input[32]
    popfd
    mov eax, DWORD PTR mw34_shadow_input[0]
    mov ecx, DWORD PTR mw34_shadow_input[4]
    mov edx, DWORD PTR mw34_shadow_input[8]
    mov ebx, DWORD PTR mw34_shadow_input[12]
    mov ebp, DWORD PTR mw34_shadow_input[20]
    mov esi, DWORD PTR mw34_shadow_input[24]
    mov edi, DWORD PTR mw34_shadow_input[28]
    mov esp, DWORD PTR mw34_shadow_input[16]
    jmp DWORD PTR mw34_shadow_entry
mw34_enter_shadow ENDP
mw34_capture_shadow PROC
    mov DWORD PTR mw34_shadow_output[0], eax
    mov DWORD PTR mw34_shadow_output[4], ecx
    mov DWORD PTR mw34_shadow_output[8], edx
    mov DWORD PTR mw34_shadow_output[12], ebx
    mov DWORD PTR mw34_shadow_output[16], esp
    mov DWORD PTR mw34_shadow_output[20], ebp
    mov DWORD PTR mw34_shadow_output[24], esi
    mov DWORD PTR mw34_shadow_output[28], edi
    mov esp, mw34_shadow_host_esp
    pushfd
    pop DWORD PTR mw34_shadow_output[32]
    mov eax, mw34_shadow_sentinel
    mov DWORD PTR mw34_shadow_output[36], eax
    popad
    popfd
    ret
mw34_capture_shadow ENDP
mw34_enter_hook_test PROC
    fxsave mw34_hook_fp_input
    pushfd
    pushad
    mov mw34_hook_host_esp, esp
    push DWORD PTR mw34_hook_input[32]
    popfd
    mov eax, DWORD PTR mw34_hook_input[0]
    mov ecx, DWORD PTR mw34_hook_input[4]
    mov edx, DWORD PTR mw34_hook_input[8]
    mov ebx, DWORD PTR mw34_hook_input[12]
    mov ebp, DWORD PTR mw34_hook_input[20]
    mov esi, DWORD PTR mw34_hook_input[24]
    mov edi, DWORD PTR mw34_hook_input[28]
    mov esp, DWORD PTR mw34_hook_input[16]
    jmp mw34_hook_entry
mw34_enter_hook_test ENDP
mw34_capture_hook_test PROC
    fxsave mw34_hook_fp_output
    mov DWORD PTR mw34_hook_output[0], eax
    mov DWORD PTR mw34_hook_output[4], ecx
    mov DWORD PTR mw34_hook_output[8], edx
    mov DWORD PTR mw34_hook_output[12], ebx
    mov DWORD PTR mw34_hook_output[16], esp
    mov DWORD PTR mw34_hook_output[20], ebp
    mov DWORD PTR mw34_hook_output[24], esi
    mov DWORD PTR mw34_hook_output[28], edi
    mov esp, mw34_hook_host_esp
    pushfd
    pop DWORD PTR mw34_hook_output[32]
    mov eax, mw34_hook_sentinel
    mov DWORD PTR mw34_hook_output[36], eax
    popad
    popfd
    ret
mw34_capture_hook_test ENDP
END
