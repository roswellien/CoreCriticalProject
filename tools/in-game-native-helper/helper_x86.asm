; Authored bridges only. The original helper instructions remain untouched.
.686p
.xmm
.model flat, C
option casemap:none
EXTERN mw34_helper_dispatch:PROC
EXTERN helper_input:BYTE
EXTERN helper_after:BYTE
EXTERN helper_host_esp:DWORD
EXTERN helper_guest_fx:BYTE
EXTERN helper_guest_env:BYTE
EXTERN helper_host_fx:BYTE
EXTERN helper_host_env:BYTE
EXTERN helper_fx_after:BYTE
EXTERN helper_env_after:BYTE
EXTERN helper_test_input:BYTE
EXTERN helper_test_after:BYTE
EXTERN helper_test_host_esp:DWORD
EXTERN helper_test_host_fx:BYTE
EXTERN helper_test_host_env:BYTE
EXTERN helper_test_fx_after:BYTE
EXTERN helper_test_env_after:BYTE
EXTERN helper_test_mxcsr:DWORD
EXTERN helper_host_mxcsr:DWORD
EXTERN helper_test_cw:WORD
EXTERN helper_test_depth:DWORD
EXTERN helper_test_xmm:BYTE
PUBLIC mw34_helper_entry
PUBLIC helper_enter
PUBLIC helper_capture
PUBLIC helper_restore
PUBLIC helper_test_enter
PUBLIC helper_test_capture
.code
mw34_helper_entry PROC
    pushfd
    pushad
    mov ebx, esp
    sub esp, 560
    and esp, -16
    mov esi, esp
    ; Capture FP/vector storage and separate legacy metadata before C++ calls.
    fxsave [esi]
    fnstenv [esi+512]
    fldenv [esi+512]
    ; C++ scratch owns a clean host FP environment; the literal guest images
    ; above are unchanged and are restored from the verified response below.
    fninit
    ldmxcsr helper_host_mxcsr
    cld
    lea eax, [esi+512]
    push eax
    push esi
    push ebx
    call mw34_helper_dispatch
    add esp, 12
    fxrstor [esi]
    fldenv [esi+512]
    mov esp, ebx
    popad
    popfd
    ret 4
mw34_helper_entry ENDP
helper_enter PROC
    pushfd
    pushad
    mov helper_host_esp, esp
    fxsave helper_host_fx
    fnstenv helper_host_env
    fldenv helper_host_env
    fxrstor helper_guest_fx
    fldenv helper_guest_env
    push DWORD PTR helper_input[32]
    popfd
    mov eax, DWORD PTR helper_input[0]
    mov ecx, DWORD PTR helper_input[4]
    mov edx, DWORD PTR helper_input[8]
    mov ebx, DWORD PTR helper_input[12]
    mov ebp, DWORD PTR helper_input[20]
    mov esi, DWORD PTR helper_input[24]
    mov edi, DWORD PTR helper_input[28]
    mov esp, DWORD PTR helper_input[16]
    jmp DWORD PTR helper_input[36]
helper_enter ENDP
helper_capture PROC
    mov DWORD PTR helper_after[0], eax
    mov DWORD PTR helper_after[4], ecx
    mov DWORD PTR helper_after[8], edx
    mov DWORD PTR helper_after[12], ebx
    mov DWORD PTR helper_after[16], esp
    mov DWORD PTR helper_after[20], ebp
    mov DWORD PTR helper_after[24], esi
    mov DWORD PTR helper_after[28], edi
    mov esp, helper_host_esp
    pushfd
    pop DWORD PTR helper_after[32]
    mov DWORD PTR helper_after[36], OFFSET helper_capture
    fxsave helper_fx_after
    fnstenv helper_env_after
    fxrstor helper_host_fx
    fldenv helper_host_env
    popad
    popfd
    ret
helper_capture ENDP
helper_restore PROC
    fxrstor helper_host_fx
    fldenv helper_host_env
    ret
helper_restore ENDP
helper_test_enter PROC
    pushfd
    pushad
    mov helper_test_host_esp, esp
    fxsave helper_test_host_fx
    fnstenv helper_test_host_env
    fldenv helper_test_host_env
    ; This authored synthetic fixture never substitutes a captured game input.
    fninit
    fldcw helper_test_cw
    ldmxcsr helper_test_mxcsr
    mov ecx, helper_test_depth
    jecxz helper_seed_vectors
helper_seed_stack:
    test ecx, 1
    jz helper_seed_zero
    fld1
    jmp helper_seed_next
helper_seed_zero:
    fldz
helper_seed_next:
    dec ecx
    jnz helper_seed_stack
helper_seed_vectors:
    movdqa xmm0, XMMWORD PTR helper_test_xmm[0]
    movdqa xmm1, XMMWORD PTR helper_test_xmm[16]
    movdqa xmm2, XMMWORD PTR helper_test_xmm[32]
    movdqa xmm3, XMMWORD PTR helper_test_xmm[48]
    movdqa xmm4, XMMWORD PTR helper_test_xmm[64]
    movdqa xmm5, XMMWORD PTR helper_test_xmm[80]
    movdqa xmm6, XMMWORD PTR helper_test_xmm[96]
    movdqa xmm7, XMMWORD PTR helper_test_xmm[112]
    push DWORD PTR helper_test_input[32]
    popfd
    mov eax, DWORD PTR helper_test_input[0]
    mov ecx, DWORD PTR helper_test_input[4]
    mov edx, DWORD PTR helper_test_input[8]
    mov ebx, DWORD PTR helper_test_input[12]
    mov ebp, DWORD PTR helper_test_input[20]
    mov esi, DWORD PTR helper_test_input[24]
    mov edi, DWORD PTR helper_test_input[28]
    mov esp, DWORD PTR helper_test_input[16]
    jmp mw34_helper_entry
helper_test_enter ENDP
helper_test_capture PROC
    mov DWORD PTR helper_test_after[0], eax
    mov DWORD PTR helper_test_after[4], ecx
    mov DWORD PTR helper_test_after[8], edx
    mov DWORD PTR helper_test_after[12], ebx
    mov DWORD PTR helper_test_after[16], esp
    mov DWORD PTR helper_test_after[20], ebp
    mov DWORD PTR helper_test_after[24], esi
    mov DWORD PTR helper_test_after[28], edi
    mov esp, helper_test_host_esp
    pushfd
    pop DWORD PTR helper_test_after[32]
    mov DWORD PTR helper_test_after[36], OFFSET helper_test_capture
    fxsave helper_test_fx_after
    fnstenv helper_test_env_after
    fxrstor helper_test_host_fx
    fldenv helper_test_host_env
    popad
    popfd
    ret
helper_test_capture ENDP
END
