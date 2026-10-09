.686p
.xmm
.model flat, C
option casemap:none
EXTERN m3_input:BYTE
EXTERN m3_before:BYTE
EXTERN m3_after:BYTE
EXTERN m3_host_esp:DWORD
EXTERN m3_guest_fx:BYTE
EXTERN m3_host_fx:BYTE
EXTERN m3_host_after:BYTE
EXTERN m3_fx_before:BYTE
EXTERN m3_fx_after:BYTE
EXTERN m3_env_before:BYTE
EXTERN m3_env_after:BYTE
EXTERN m3_host_env:BYTE
EXTERN m3_host_env_after:BYTE
PUBLIC m3_enter
PUBLIC m3_capture
PUBLIC m3_restore_fp
.code
m3_enter PROC
 pushfd
 pushad
 mov m3_host_esp,esp
 fxsave m3_host_fx
 fnstenv m3_host_env
 fxrstor m3_guest_fx
 fxsave m3_fx_before
 fnstenv m3_env_before
 push DWORD PTR m3_input[32]
 popfd
 mov eax,DWORD PTR m3_input[0]
 mov ecx,DWORD PTR m3_input[4]
 mov edx,DWORD PTR m3_input[8]
 mov ebx,DWORD PTR m3_input[12]
 mov ebp,DWORD PTR m3_input[20]
 mov esi,DWORD PTR m3_input[24]
 mov edi,DWORD PTR m3_input[28]
 mov esp,DWORD PTR m3_input[16]
 ; Actual entry GPR/flags capture. MOV preserves flags and guest register values.
 mov DWORD PTR m3_before[0],eax
 mov DWORD PTR m3_before[4],ecx
 mov DWORD PTR m3_before[8],edx
 mov DWORD PTR m3_before[12],ebx
 mov DWORD PTR m3_before[16],esp
 mov DWORD PTR m3_before[20],ebp
 mov DWORD PTR m3_before[24],esi
 mov DWORD PTR m3_before[28],edi
 mov esp,m3_host_esp
 pushfd
 pop DWORD PTR m3_before[32]
 mov DWORD PTR m3_before[36],558290h
 mov esp,DWORD PTR m3_input[16]
 jmp DWORD PTR m3_input[36]
m3_enter ENDP
m3_capture PROC
 mov DWORD PTR m3_after[0],eax
 mov DWORD PTR m3_after[4],ecx
 mov DWORD PTR m3_after[8],edx
 mov DWORD PTR m3_after[12],ebx
 mov DWORD PTR m3_after[16],esp
 mov DWORD PTR m3_after[20],ebp
 mov DWORD PTR m3_after[24],esi
 mov DWORD PTR m3_after[28],edi
 mov esp,m3_host_esp
 pushfd
 pop DWORD PTR m3_after[32]
 mov DWORD PTR m3_after[36],10000100h
 ; Direct hardware captures, before any C++ or SIMD operation.
 fxsave m3_fx_after
 fnstenv m3_env_after
 fxrstor m3_host_fx
 fldenv m3_host_env
 fxsave m3_host_after
 fnstenv m3_host_env_after
 fldenv m3_host_env
 popad
 popfd
 ret
m3_capture ENDP
m3_restore_fp PROC
 ; Only original hardware-fault containment; never counted as body success.
 fxrstor m3_host_fx
 fldenv m3_host_env
 fxsave m3_host_after
 fnstenv m3_host_env_after
 fldenv m3_host_env
 ret
m3_restore_fp ENDP
END
