.686p
.xmm
.model flat, C
option casemap:none
EXTERN m4_input:BYTE
EXTERN m4_before:BYTE
EXTERN m4_after:BYTE
EXTERN m4_host_esp:DWORD
EXTERN m4_guest_fx:BYTE
EXTERN m4_host_fx:BYTE
EXTERN m4_host_after:BYTE
EXTERN m4_fx_before:BYTE
EXTERN m4_fx_after:BYTE
EXTERN m4_env_before:BYTE
EXTERN m4_env_after:BYTE
EXTERN m4_host_env:BYTE
EXTERN m4_host_env_after:BYTE
PUBLIC m4_enter
PUBLIC m4_capture
PUBLIC m4_restore_fp
.code
m4_enter PROC
 pushfd
 pushad
 mov m4_host_esp,esp
 fxsave m4_host_fx
 fnstenv m4_host_env
 fxrstor m4_guest_fx
 fxsave m4_fx_before
 fnstenv m4_env_before
 push DWORD PTR m4_input[32]
 popfd
 mov eax,DWORD PTR m4_input[0]
 mov ecx,DWORD PTR m4_input[4]
 mov edx,DWORD PTR m4_input[8]
 mov ebx,DWORD PTR m4_input[12]
 mov ebp,DWORD PTR m4_input[20]
 mov esi,DWORD PTR m4_input[24]
 mov edi,DWORD PTR m4_input[28]
 mov esp,DWORD PTR m4_input[16]
 ; Actual entry GPR/flags capture. MOV preserves flags and guest register values.
 mov DWORD PTR m4_before[0],eax
 mov DWORD PTR m4_before[4],ecx
 mov DWORD PTR m4_before[8],edx
 mov DWORD PTR m4_before[12],ebx
 mov DWORD PTR m4_before[16],esp
 mov DWORD PTR m4_before[20],ebp
 mov DWORD PTR m4_before[24],esi
 mov DWORD PTR m4_before[28],edi
 mov esp,m4_host_esp
 pushfd
 pop DWORD PTR m4_before[32]
 mov DWORD PTR m4_before[36],410910h
 mov esp,DWORD PTR m4_input[16]
 jmp DWORD PTR m4_input[36]
m4_enter ENDP
m4_capture PROC
 mov DWORD PTR m4_after[0],eax
 mov DWORD PTR m4_after[4],ecx
 mov DWORD PTR m4_after[8],edx
 mov DWORD PTR m4_after[12],ebx
 mov DWORD PTR m4_after[16],esp
 mov DWORD PTR m4_after[20],ebp
 mov DWORD PTR m4_after[24],esi
 mov DWORD PTR m4_after[28],edi
 mov esp,m4_host_esp
 pushfd
 pop DWORD PTR m4_after[32]
 mov DWORD PTR m4_after[36],10000100h
 ; Direct hardware captures, before any C++ or SIMD operation.
 fxsave m4_fx_after
 fnstenv m4_env_after
 fxrstor m4_host_fx
 fldenv m4_host_env
 fxsave m4_host_after
 fnstenv m4_host_env_after
 fldenv m4_host_env
 popad
 popfd
 ret
m4_capture ENDP
m4_restore_fp PROC
 ; Only original hardware-fault containment; never counted as body success.
 fxrstor m4_host_fx
 fldenv m4_host_env
 fxsave m4_host_after
 fnstenv m4_host_env_after
 fldenv m4_host_env
 ret
m4_restore_fp ENDP
END
