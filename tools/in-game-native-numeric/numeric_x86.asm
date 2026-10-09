; Authored bridges only. The admitted game and provider instructions stay intact.
.686p
.xmm
.model flat, C
option casemap:none
EXTERN mw34_numeric_dispatch:PROC
EXTERN numeric_input:BYTE
EXTERN numeric_after:BYTE
EXTERN numeric_host_esp:DWORD
EXTERN numeric_guest_fx:BYTE
EXTERN numeric_guest_env:BYTE
EXTERN numeric_host_fx:BYTE
EXTERN numeric_host_env:BYTE
EXTERN numeric_fx_after:BYTE
EXTERN numeric_env_after:BYTE
EXTERN numeric_test_input:BYTE
EXTERN numeric_test_after:BYTE
EXTERN numeric_test_host_esp:DWORD
EXTERN numeric_test_host_fx:BYTE
EXTERN numeric_test_host_env:BYTE
EXTERN numeric_test_fx_after:BYTE
EXTERN numeric_test_env_after:BYTE
EXTERN numeric_test_mxcsr:DWORD
PUBLIC mw34_numeric_entry
PUBLIC numeric_enter
PUBLIC numeric_capture
PUBLIC numeric_restore
PUBLIC numeric_test_enter
PUBLIC numeric_test_capture
.code
mw34_numeric_entry PROC
    pushfd
    pushad
    mov ebx, esp
    sub esp, 560
    and esp, -16
    mov esi, esp
    ; Capture both hardware storage and separate legacy metadata before C++.
    fxsave [esi]
    fnstenv [esi+512]
    fldenv [esi+512]
    cld
    lea eax, [esi+512]
    push eax
    push esi
    push ebx
    call mw34_numeric_dispatch
    add esp, 12
    ; Dispatch publishes verified native storage and metadata in these locals.
    fxrstor [esi]
    fldenv [esi+512]
    mov esp, ebx
    popad
    popfd
    ret
mw34_numeric_entry ENDP
numeric_enter PROC
    pushfd
    pushad
    mov numeric_host_esp, esp
    fxsave numeric_host_fx
    fnstenv numeric_host_env
    fldenv numeric_host_env
    fxrstor numeric_guest_fx
    fldenv numeric_guest_env
    push DWORD PTR numeric_input[32]
    popfd
    mov eax, DWORD PTR numeric_input[0]
    mov ecx, DWORD PTR numeric_input[4]
    mov edx, DWORD PTR numeric_input[8]
    mov ebx, DWORD PTR numeric_input[12]
    mov ebp, DWORD PTR numeric_input[20]
    mov esi, DWORD PTR numeric_input[24]
    mov edi, DWORD PTR numeric_input[28]
    mov esp, DWORD PTR numeric_input[16]
    jmp DWORD PTR numeric_input[36]
numeric_enter ENDP
numeric_capture PROC
    mov DWORD PTR numeric_after[0], eax
    mov DWORD PTR numeric_after[4], ecx
    mov DWORD PTR numeric_after[8], edx
    mov DWORD PTR numeric_after[12], ebx
    mov DWORD PTR numeric_after[16], esp
    mov DWORD PTR numeric_after[20], ebp
    mov DWORD PTR numeric_after[24], esi
    mov DWORD PTR numeric_after[28], edi
    mov esp, numeric_host_esp
    pushfd
    pop DWORD PTR numeric_after[32]
    mov DWORD PTR numeric_after[36], OFFSET numeric_capture
    fxsave numeric_fx_after
    fnstenv numeric_env_after
    fxrstor numeric_host_fx
    fldenv numeric_host_env
    popad
    popfd
    ret
numeric_capture ENDP
numeric_restore PROC
    fxrstor numeric_host_fx
    fldenv numeric_host_env
    ret
numeric_restore ENDP
numeric_test_enter PROC
    pushfd
    pushad
    mov numeric_test_host_esp, esp
    fxsave numeric_test_host_fx
    fnstenv numeric_test_host_env
    fldenv numeric_test_host_env
    ; An explicitly authored depth-zero fixture, never an observed game call.
    fninit
    ldmxcsr numeric_test_mxcsr
    push DWORD PTR numeric_test_input[32]
    popfd
    mov eax, DWORD PTR numeric_test_input[0]
    mov ecx, DWORD PTR numeric_test_input[4]
    mov edx, DWORD PTR numeric_test_input[8]
    mov ebx, DWORD PTR numeric_test_input[12]
    mov ebp, DWORD PTR numeric_test_input[20]
    mov esi, DWORD PTR numeric_test_input[24]
    mov edi, DWORD PTR numeric_test_input[28]
    mov esp, DWORD PTR numeric_test_input[16]
    jmp mw34_numeric_entry
numeric_test_enter ENDP
numeric_test_capture PROC
    mov DWORD PTR numeric_test_after[0], eax
    mov DWORD PTR numeric_test_after[4], ecx
    mov DWORD PTR numeric_test_after[8], edx
    mov DWORD PTR numeric_test_after[12], ebx
    mov DWORD PTR numeric_test_after[16], esp
    mov DWORD PTR numeric_test_after[20], ebp
    mov DWORD PTR numeric_test_after[24], esi
    mov DWORD PTR numeric_test_after[28], edi
    mov esp, numeric_test_host_esp
    pushfd
    pop DWORD PTR numeric_test_after[32]
    mov DWORD PTR numeric_test_after[36], OFFSET numeric_test_capture
    fxsave numeric_test_fx_after
    fnstenv numeric_test_env_after
    fxrstor numeric_test_host_fx
    fldenv numeric_test_host_env
    popad
    popfd
    ret
numeric_test_capture ENDP
END
