.686p
.xmm
.model flat,C
option casemap:none
EXTERN mixed_host_esp:DWORD
EXTERN b_cpu:BYTE
EXTERN b_fx:BYTE
EXTERN b_env:BYTE
EXTERN b_pc:DWORD
EXTERN b_resume:DWORD
EXTERN observe_boundary:PROC
EXTERN source_next_b5:DWORD
EXTERN source_next_c0:DWORD
PUBLIC mfc_enter_hook
PUBLIC mfc_return_hook
PUBLIC field_hook
PUBLIC mbcp_enter_hook
PUBLIC mbcp_return_hook
.code
capture_boundary:
 mov DWORD PTR b_cpu[0],eax
 mov DWORD PTR b_cpu[4],ecx
 mov DWORD PTR b_cpu[8],edx
 mov DWORD PTR b_cpu[12],ebx
 mov DWORD PTR b_cpu[16],esp
 mov DWORD PTR b_cpu[20],ebp
 mov DWORD PTR b_cpu[24],esi
 mov DWORD PTR b_cpu[28],edi
 mov esp,mixed_host_esp
 pushfd
 pop DWORD PTR b_cpu[32]
 mov eax,b_pc
 mov DWORD PTR b_cpu[36],eax
 fxsave b_fx
 fnstenv b_env
 fldenv b_env
 cld
 call observe_boundary
 fxrstor b_fx
 fldenv b_env
 push DWORD PTR b_cpu[32]
 popfd
 mov eax,DWORD PTR b_cpu[0]
 mov ecx,DWORD PTR b_cpu[4]
 mov edx,DWORD PTR b_cpu[8]
 mov ebx,DWORD PTR b_cpu[12]
 mov ebp,DWORD PTR b_cpu[20]
 mov esi,DWORD PTR b_cpu[24]
 mov edi,DWORD PTR b_cpu[28]
 mov esp,DWORD PTR b_cpu[16]
 jmp b_resume
mfc_enter_hook PROC
 push 005ae3adh
 mov b_pc,05f401083h
 mov b_resume,OFFSET mfc_enter_go
 jmp capture_boundary
mfc_enter_go:
 jmp DWORD PTR ds:[005bb210h]
mfc_enter_hook ENDP
mfc_return_hook PROC
 mov b_pc,005ae3adh
 mov b_resume,OFFSET mfc_return_go
 jmp capture_boundary
mfc_return_go:
 mov ecx,DWORD PTR [esp+4]
 mov edx,DWORD PTR [esp+8]
 jmp source_next_b5
mfc_return_hook ENDP
field_hook PROC
 mov b_pc,005ae3b7h
 mov b_resume,OFFSET field_first
 jmp capture_boundary
field_first:
 mov BYTE PTR [eax+14h],cl
 mov b_pc,005ae3bah
 mov b_resume,OFFSET field_second
 jmp capture_boundary
field_second:
 mov DWORD PTR [eax+1040h],edx
 mov b_pc,005ae3c0h
 mov b_resume,OFFSET field_done
 jmp capture_boundary
field_done:
 jmp source_next_c0
field_hook ENDP
mbcp_enter_hook PROC
 push 005ae3cah
 mov b_pc,078003ddbh
 mov b_resume,OFFSET mbcp_enter_go
 jmp capture_boundary
mbcp_enter_go:
 jmp DWORD PTR ds:[005bb674h]
mbcp_enter_hook ENDP
mbcp_return_hook PROC
 mov b_pc,005ae3cah
 mov b_resume,OFFSET mbcp_return_go
 jmp capture_boundary
mbcp_return_go:
 pop ecx
 push 1
 pop eax
 ret 8
mbcp_return_hook ENDP
END
