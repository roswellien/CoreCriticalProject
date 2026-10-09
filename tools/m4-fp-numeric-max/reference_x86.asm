.686p
.xmm
.model flat, C
option casemap:none
EXTERN numeric_input:BYTE
EXTERN numeric_before:BYTE
EXTERN numeric_after:BYTE
EXTERN numeric_host_esp:DWORD
EXTERN numeric_guest_fx:BYTE
EXTERN numeric_guest_env:BYTE
EXTERN numeric_env_ready:DWORD
EXTERN numeric_host_fx:BYTE
EXTERN numeric_host_after:BYTE
EXTERN numeric_fx_before:BYTE
EXTERN numeric_fx_after:BYTE
EXTERN numeric_env_before:BYTE
EXTERN numeric_env_after:BYTE
EXTERN numeric_host_env:BYTE
EXTERN numeric_host_env_after:BYTE
PUBLIC numeric_enter
PUBLIC numeric_capture
PUBLIC numeric_restore
.code
numeric_enter PROC
 pushfd
 pushad
 mov numeric_host_esp,esp
 fxsave numeric_host_fx
 fnstenv numeric_host_env
 fxrstor numeric_guest_fx
 cmp numeric_env_ready,0
 je first_environment
 ; Hardware FX storage and legacy x87 metadata have separate provenance.
 ; Carry both from the previous actual body; no initial metadata is invented.
 fldenv numeric_guest_env
first_environment:
 fxsave numeric_fx_before
 fnstenv numeric_env_before
 push DWORD PTR numeric_input[32]
 popfd
 mov eax,DWORD PTR numeric_input[0]
 mov ecx,DWORD PTR numeric_input[4]
 mov edx,DWORD PTR numeric_input[8]
 mov ebx,DWORD PTR numeric_input[12]
 mov ebp,DWORD PTR numeric_input[20]
 mov esi,DWORD PTR numeric_input[24]
 mov edi,DWORD PTR numeric_input[28]
 mov esp,DWORD PTR numeric_input[16]
 mov DWORD PTR numeric_before[0],eax
 mov DWORD PTR numeric_before[4],ecx
 mov DWORD PTR numeric_before[8],edx
 mov DWORD PTR numeric_before[12],ebx
 mov DWORD PTR numeric_before[16],esp
 mov DWORD PTR numeric_before[20],ebp
 mov DWORD PTR numeric_before[24],esi
 mov DWORD PTR numeric_before[28],edi
 mov esp,numeric_host_esp
 pushfd
 pop DWORD PTR numeric_before[32]
 mov esp,DWORD PTR numeric_input[36]
 mov DWORD PTR numeric_before[36],esp
 mov esp,DWORD PTR numeric_input[16]
 jmp DWORD PTR numeric_input[36]
numeric_enter ENDP
numeric_capture PROC
 mov DWORD PTR numeric_after[0],eax
 mov DWORD PTR numeric_after[4],ecx
 mov DWORD PTR numeric_after[8],edx
 mov DWORD PTR numeric_after[12],ebx
 mov DWORD PTR numeric_after[16],esp
 mov DWORD PTR numeric_after[20],ebp
 mov DWORD PTR numeric_after[24],esi
 mov DWORD PTR numeric_after[28],edi
 mov esp,numeric_host_esp
 pushfd
 pop DWORD PTR numeric_after[32]
 ; Only the agreed authored JMP capture broker reaches this label normally.
 mov DWORD PTR numeric_after[36],010000100h
 fxsave numeric_fx_after
 fnstenv numeric_env_after
 fxrstor numeric_host_fx
 fldenv numeric_host_env
 fxsave numeric_host_after
 fnstenv numeric_host_env_after
 fldenv numeric_host_env
 popad
 popfd
 ret
numeric_capture ENDP
numeric_restore PROC
 ; Fault containment only. This route never grants successful body credit.
 fxrstor numeric_host_fx
 fldenv numeric_host_env
 fxsave numeric_host_after
 fnstenv numeric_host_env_after
 fldenv numeric_host_env
 ret
numeric_restore ENDP
END
