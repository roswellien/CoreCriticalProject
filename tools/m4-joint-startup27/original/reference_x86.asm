.686p
.xmm
.model flat, C
option casemap:none
EXTERN mixed_input:BYTE
EXTERN mixed_before:BYTE
EXTERN mixed_after:BYTE
EXTERN mixed_host_esp:DWORD
EXTERN mixed_guest_fx:BYTE
EXTERN mixed_guest_env:BYTE
EXTERN mixed_env_ready:DWORD
EXTERN mixed_host_fx:BYTE
EXTERN mixed_host_after:BYTE
EXTERN mixed_fx_before:BYTE
EXTERN mixed_fx_after:BYTE
EXTERN mixed_env_before:BYTE
EXTERN mixed_env_after:BYTE
EXTERN mixed_host_env:BYTE
EXTERN mixed_host_env_after:BYTE
PUBLIC mixed_enter
PUBLIC mixed_capture
PUBLIC mixed_restore
.code
mixed_enter PROC
 pushfd
 pushad
 mov mixed_host_esp,esp
 fxsave mixed_host_fx
 fnstenv mixed_host_env
 fxrstor mixed_guest_fx
 cmp mixed_env_ready,0
 je first_environment
 ; Hardware FX storage and legacy x87 metadata have separate provenance.
 ; Carry both from the previous actual body; no initial metadata is invented.
 fldenv mixed_guest_env
first_environment:
 fxsave mixed_fx_before
 fnstenv mixed_env_before
 push DWORD PTR mixed_input[32]
 popfd
 mov eax,DWORD PTR mixed_input[0]
 mov ecx,DWORD PTR mixed_input[4]
 mov edx,DWORD PTR mixed_input[8]
 mov ebx,DWORD PTR mixed_input[12]
 mov ebp,DWORD PTR mixed_input[20]
 mov esi,DWORD PTR mixed_input[24]
 mov edi,DWORD PTR mixed_input[28]
 mov esp,DWORD PTR mixed_input[16]
 mov DWORD PTR mixed_before[0],eax
 mov DWORD PTR mixed_before[4],ecx
 mov DWORD PTR mixed_before[8],edx
 mov DWORD PTR mixed_before[12],ebx
 mov DWORD PTR mixed_before[16],esp
 mov DWORD PTR mixed_before[20],ebp
 mov DWORD PTR mixed_before[24],esi
 mov DWORD PTR mixed_before[28],edi
 mov esp,mixed_host_esp
 pushfd
 pop DWORD PTR mixed_before[32]
 mov esp,DWORD PTR mixed_input[36]
 mov DWORD PTR mixed_before[36],esp
 mov esp,DWORD PTR mixed_input[16]
 jmp DWORD PTR mixed_input[36]
mixed_enter ENDP
mixed_capture PROC
 mov DWORD PTR mixed_after[0],eax
 mov DWORD PTR mixed_after[4],ecx
 mov DWORD PTR mixed_after[8],edx
 mov DWORD PTR mixed_after[12],ebx
 mov DWORD PTR mixed_after[16],esp
 mov DWORD PTR mixed_after[20],ebp
 mov DWORD PTR mixed_after[24],esi
 mov DWORD PTR mixed_after[28],edi
 mov esp,mixed_host_esp
 pushfd
 pop DWORD PTR mixed_after[32]
 ; Only the agreed authored JMP capture broker reaches this label normally.
 mov DWORD PTR mixed_after[36],00410a80h
 fxsave mixed_fx_after
 fnstenv mixed_env_after
 fxrstor mixed_host_fx
 fldenv mixed_host_env
 fxsave mixed_host_after
 fnstenv mixed_host_env_after
 fldenv mixed_host_env
 popad
 popfd
 ret
mixed_capture ENDP
mixed_restore PROC
 ; Fault containment only. This route never grants successful body credit.
 fxrstor mixed_host_fx
 fldenv mixed_host_env
 fxsave mixed_host_after
 fnstenv mixed_host_env_after
 fldenv mixed_host_env
 ret
mixed_restore ENDP
END
