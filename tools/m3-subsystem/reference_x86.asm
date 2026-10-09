.686p
.xmm
.model flat, C
option casemap:none
EXTERN s3_input:BYTE
EXTERN s3_before:BYTE
EXTERN s3_after:BYTE
EXTERN s3_host_esp:DWORD
EXTERN s3_guest_fx:BYTE
EXTERN s3_guest_env:BYTE
EXTERN s3_host_fx:BYTE
EXTERN s3_host_after:BYTE
EXTERN s3_fx_before:BYTE
EXTERN s3_fx_after:BYTE
EXTERN s3_env_before:BYTE
EXTERN s3_env_after:BYTE
EXTERN s3_host_env:BYTE
EXTERN s3_host_env_after:BYTE
PUBLIC s3_enter
PUBLIC s3_capture
PUBLIC s3_restore_fp
.code
s3_enter PROC
 pushfd
 pushad
 mov s3_host_esp,esp
 fxsave s3_host_fx
 fnstenv s3_host_env
 fxrstor s3_guest_fx
 fldenv s3_guest_env
 fxsave s3_fx_before
 fnstenv s3_env_before
 push DWORD PTR s3_input[32]
 popfd
 mov eax,DWORD PTR s3_input[0]
 mov ecx,DWORD PTR s3_input[4]
 mov edx,DWORD PTR s3_input[8]
 mov ebx,DWORD PTR s3_input[12]
 mov ebp,DWORD PTR s3_input[20]
 mov esi,DWORD PTR s3_input[24]
 mov edi,DWORD PTR s3_input[28]
 mov esp,DWORD PTR s3_input[16]
 ; Actual entry GPR/flags capture. MOV preserves flags and guest register values.
 mov DWORD PTR s3_before[0],eax
 mov DWORD PTR s3_before[4],ecx
 mov DWORD PTR s3_before[8],edx
 mov DWORD PTR s3_before[12],ebx
 mov DWORD PTR s3_before[16],esp
 mov DWORD PTR s3_before[20],ebp
 mov DWORD PTR s3_before[24],esi
 mov DWORD PTR s3_before[28],edi
 mov esp,s3_host_esp
 pushfd
 pop DWORD PTR s3_before[32]
 mov eax,DWORD PTR s3_input[36]
 mov DWORD PTR s3_before[36],eax
 mov eax,DWORD PTR s3_input[0]
 mov esp,DWORD PTR s3_input[16]
 jmp DWORD PTR s3_input[36]
s3_enter ENDP
s3_capture PROC
 mov DWORD PTR s3_after[0],eax
 mov DWORD PTR s3_after[4],ecx
 mov DWORD PTR s3_after[8],edx
 mov DWORD PTR s3_after[12],ebx
 mov DWORD PTR s3_after[16],esp
 mov DWORD PTR s3_after[20],ebp
 mov DWORD PTR s3_after[24],esi
 mov DWORD PTR s3_after[28],edi
 mov esp,s3_host_esp
 pushfd
 pop DWORD PTR s3_after[32]
 mov DWORD PTR s3_after[36],10000100h
 ; Direct hardware captures, before any C++ or SIMD operation.
 fxsave s3_fx_after
 fnstenv s3_env_after
 fxrstor s3_host_fx
 fldenv s3_host_env
 fxsave s3_host_after
 fnstenv s3_host_env_after
 fldenv s3_host_env
 popad
 popfd
 ret
s3_capture ENDP
s3_restore_fp PROC
 ; Only original hardware-fault containment; never counted as body success.
 fxrstor s3_host_fx
 fldenv s3_host_env
 fxsave s3_host_after
 fnstenv s3_host_env_after
 fldenv s3_host_env
 ret
s3_restore_fp ENDP
END
