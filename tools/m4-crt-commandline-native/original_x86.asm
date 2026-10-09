.686p
.xmm
.model flat, C
option casemap:none
EXTERN crt_input:BYTE
EXTERN crt_before:BYTE
EXTERN crt_after:BYTE
EXTERN crt_host_esp:DWORD
EXTERN crt_guest_fx:BYTE
EXTERN crt_guest_env:BYTE
EXTERN crt_host_fx:BYTE
EXTERN crt_host_after:BYTE
EXTERN crt_fx_before:BYTE
EXTERN crt_fx_after:BYTE
EXTERN crt_env_before:BYTE
EXTERN crt_env_after:BYTE
EXTERN crt_host_env:BYTE
EXTERN crt_host_env_after:BYTE
EXTERN cmd_service_before:BYTE
EXTERN cmd_service_after:BYTE
EXTERN cmd_api:DWORD
EXTERN cmd_service_fx_before:BYTE
EXTERN cmd_service_fx_after:BYTE
EXTERN cmd_service_env_before:BYTE
EXTERN cmd_service_env_after:BYTE
PUBLIC cmd_service
PUBLIC crt_enter
PUBLIC crt_capture
PUBLIC crt_restore
.code
crt_enter PROC
 pushfd
 pushad
 mov crt_host_esp,esp
 fxsave crt_host_fx
 fnstenv crt_host_env
 fxrstor crt_guest_fx
 fldenv crt_guest_env
 fxsave crt_fx_before
 fnstenv crt_env_before
 push DWORD PTR crt_input[32]
 popfd
 mov eax,DWORD PTR crt_input[0]
 mov ecx,DWORD PTR crt_input[4]
 mov edx,DWORD PTR crt_input[8]
 mov ebx,DWORD PTR crt_input[12]
 mov ebp,DWORD PTR crt_input[20]
 mov esi,DWORD PTR crt_input[24]
 mov edi,DWORD PTR crt_input[28]
 mov esp,DWORD PTR crt_input[16]
 ; Actual entry GPR/flags capture. MOV preserves flags and guest register values.
 mov DWORD PTR crt_before[0],eax
 mov DWORD PTR crt_before[4],ecx
 mov DWORD PTR crt_before[8],edx
 mov DWORD PTR crt_before[12],ebx
 mov DWORD PTR crt_before[16],esp
 mov DWORD PTR crt_before[20],ebp
 mov DWORD PTR crt_before[24],esi
 mov DWORD PTR crt_before[28],edi
 mov esp,crt_host_esp
 pushfd
 pop DWORD PTR crt_before[32]
 mov esp,DWORD PTR crt_input[36]
 mov DWORD PTR crt_before[36],esp
 mov esp,DWORD PTR crt_input[16]
 jmp DWORD PTR crt_input[36]
crt_enter ENDP
crt_capture PROC
 mov DWORD PTR crt_after[0],eax
 mov DWORD PTR crt_after[4],ecx
 mov DWORD PTR crt_after[8],edx
 mov DWORD PTR crt_after[12],ebx
 mov DWORD PTR crt_after[16],esp
 mov DWORD PTR crt_after[20],ebp
 mov DWORD PTR crt_after[24],esi
 mov DWORD PTR crt_after[28],edi
 mov esp,crt_host_esp
 pushfd
 pop DWORD PTR crt_after[32]
 mov DWORD PTR crt_after[36],10000100h
 ; Direct hardware captures, before any C++ or SIMD operation.
 fxsave crt_fx_after
 fnstenv crt_env_after
 fxrstor crt_host_fx
 fldenv crt_host_env
 fxsave crt_host_after
 fnstenv crt_host_env_after
 fldenv crt_host_env
 popad
 popfd
 ret
crt_capture ENDP
cmd_service PROC
 mov DWORD PTR cmd_service_before[0],eax
 mov DWORD PTR cmd_service_before[4],ecx
 mov DWORD PTR cmd_service_before[8],edx
 mov DWORD PTR cmd_service_before[12],ebx
 mov DWORD PTR cmd_service_before[16],esp
 mov DWORD PTR cmd_service_before[20],ebp
 mov DWORD PTR cmd_service_before[24],esi
 mov DWORD PTR cmd_service_before[28],edi
 mov esp,crt_host_esp
 pushfd
 pop DWORD PTR cmd_service_before[32]
 mov DWORD PTR cmd_service_before[36],10000200h
 fxsave cmd_service_fx_before
 fnstenv cmd_service_env_before
 fldenv cmd_service_env_before
 mov esp,DWORD PTR cmd_service_before[16]
 call DWORD PTR cmd_api
 mov DWORD PTR cmd_service_after[0],eax
 mov DWORD PTR cmd_service_after[4],ecx
 mov DWORD PTR cmd_service_after[8],edx
 mov DWORD PTR cmd_service_after[12],ebx
 mov DWORD PTR cmd_service_after[16],esp
 mov DWORD PTR cmd_service_after[20],ebp
 mov DWORD PTR cmd_service_after[24],esi
 mov DWORD PTR cmd_service_after[28],edi
 mov esp,crt_host_esp
 pushfd
 pop DWORD PTR cmd_service_after[32]
 mov DWORD PTR cmd_service_after[36],10000200h
 fxsave cmd_service_fx_after
 fnstenv cmd_service_env_after
 fldenv cmd_service_env_after
 mov esp,DWORD PTR cmd_service_after[16]
 ret
cmd_service ENDP
crt_restore PROC
 ; Only original hardware-fault containment; never counted as body success.
 fxrstor crt_host_fx
 fldenv crt_host_env
 fxsave crt_host_after
 fnstenv crt_host_env_after
 fldenv crt_host_env
 ret
crt_restore ENDP
END
