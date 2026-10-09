.686p
.xmm
.model flat, C
option casemap:none
EXTERN fp_input:BYTE
EXTERN fp_before:BYTE
EXTERN fp_after:BYTE
EXTERN fp_host_esp:DWORD
EXTERN fp_guest_fx:BYTE
EXTERN fp_host_fx:BYTE
EXTERN fp_host_after:BYTE
EXTERN fp_fx_before:BYTE
EXTERN fp_fx_after:BYTE
EXTERN fp_env_before:BYTE
EXTERN fp_env_after:BYTE
EXTERN fp_host_env:BYTE
EXTERN fp_host_env_after:BYTE
PUBLIC fp_enter
PUBLIC fp_capture
PUBLIC fp_restore
.code
fp_enter PROC
 pushfd
 pushad
 mov fp_host_esp,esp
 fxsave fp_host_fx
 fnstenv fp_host_env
 fxrstor fp_guest_fx
 fxsave fp_fx_before
 fnstenv fp_env_before
 push DWORD PTR fp_input[32]
 popfd
 mov eax,DWORD PTR fp_input[0]
 mov ecx,DWORD PTR fp_input[4]
 mov edx,DWORD PTR fp_input[8]
 mov ebx,DWORD PTR fp_input[12]
 mov ebp,DWORD PTR fp_input[20]
 mov esi,DWORD PTR fp_input[24]
 mov edi,DWORD PTR fp_input[28]
 mov esp,DWORD PTR fp_input[16]
 ; Actual entry GPR/flags capture. MOV preserves flags and guest register values.
 mov DWORD PTR fp_before[0],eax
 mov DWORD PTR fp_before[4],ecx
 mov DWORD PTR fp_before[8],edx
 mov DWORD PTR fp_before[12],ebx
 mov DWORD PTR fp_before[16],esp
 mov DWORD PTR fp_before[20],ebp
 mov DWORD PTR fp_before[24],esi
 mov DWORD PTR fp_before[28],edi
 mov esp,fp_host_esp
 pushfd
 pop DWORD PTR fp_before[32]
 mov esp,DWORD PTR fp_input[36]
 mov DWORD PTR fp_before[36],esp
 mov esp,DWORD PTR fp_input[16]
 jmp DWORD PTR fp_input[36]
fp_enter ENDP
fp_capture PROC
 mov DWORD PTR fp_after[0],eax
 mov DWORD PTR fp_after[4],ecx
 mov DWORD PTR fp_after[8],edx
 mov DWORD PTR fp_after[12],ebx
 mov DWORD PTR fp_after[16],esp
 mov DWORD PTR fp_after[20],ebp
 mov DWORD PTR fp_after[24],esi
 mov DWORD PTR fp_after[28],edi
 mov esp,fp_host_esp
 pushfd
 pop DWORD PTR fp_after[32]
 mov DWORD PTR fp_after[36],10000100h
 ; Direct hardware captures, before any C++ or SIMD operation.
 fxsave fp_fx_after
 fnstenv fp_env_after
 fxrstor fp_host_fx
 fldenv fp_host_env
 fxsave fp_host_after
 fnstenv fp_host_env_after
 fldenv fp_host_env
 popad
 popfd
 ret
fp_capture ENDP
fp_restore PROC
 ; Only original hardware-fault containment; never counted as body success.
 fxrstor fp_host_fx
 fldenv fp_host_env
 fxsave fp_host_after
 fnstenv fp_host_env_after
 fldenv fp_host_env
 ret
fp_restore ENDP
END
