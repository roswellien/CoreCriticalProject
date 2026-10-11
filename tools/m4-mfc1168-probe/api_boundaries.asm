.686p
.xmm
.model flat,C
option casemap:none
EXTERN mixed_host_esp:DWORD
EXTERN a_cpu:BYTE
EXTERN a_fx:BYTE
EXTERN a_env:BYTE
EXTERN api_kind:DWORD
EXTERN api_phase:DWORD
EXTERN api_resume:DWORD
EXTERN named_targets:DWORD
EXTERN named_returns:DWORD
EXTERN observe_named_API:PROC
PUBLIC named_API_0
PUBLIC named_API_1
PUBLIC named_API_2
PUBLIC named_API_3
.code
named_capture:
 mov DWORD PTR a_cpu[0],eax
 mov DWORD PTR a_cpu[4],ecx
 mov DWORD PTR a_cpu[8],edx
 mov DWORD PTR a_cpu[12],ebx
 mov DWORD PTR a_cpu[16],esp
 mov DWORD PTR a_cpu[20],ebp
 mov DWORD PTR a_cpu[24],esi
 mov DWORD PTR a_cpu[28],edi
 mov esp,mixed_host_esp
 pushfd
 pop DWORD PTR a_cpu[32]
 fxsave a_fx
 fnstenv a_env
 fldenv a_env
 cld
 call observe_named_API
 fxrstor a_fx
 fldenv a_env
 push DWORD PTR a_cpu[32]
 popfd
 mov eax,DWORD PTR a_cpu[0]
 mov ecx,DWORD PTR a_cpu[4]
 mov edx,DWORD PTR a_cpu[8]
 mov ebx,DWORD PTR a_cpu[12]
 mov ebp,DWORD PTR a_cpu[20]
 mov esi,DWORD PTR a_cpu[24]
 mov edi,DWORD PTR a_cpu[28]
 mov esp,DWORD PTR a_cpu[16]
 jmp api_resume
named_API_0 PROC
 mov api_kind,0
 mov api_phase,0
 mov api_resume,OFFSET named_0_go
 jmp named_capture
named_0_go:
 mov DWORD PTR [esp],OFFSET named_0_return
 jmp DWORD PTR named_targets[0]
named_0_return:
 mov api_kind,0
 mov api_phase,1
 mov api_resume,OFFSET named_0_done
 jmp named_capture
named_0_done:
 jmp DWORD PTR named_returns[0]
named_API_0 ENDP
named_API_1 PROC
 mov api_kind,1
 mov api_phase,0
 mov api_resume,OFFSET named_1_go
 jmp named_capture
named_1_go:
 mov DWORD PTR [esp],OFFSET named_1_return
 jmp DWORD PTR named_targets[4]
named_1_return:
 mov api_kind,1
 mov api_phase,1
 mov api_resume,OFFSET named_1_done
 jmp named_capture
named_1_done:
 jmp DWORD PTR named_returns[4]
named_API_1 ENDP
named_API_2 PROC
 mov api_kind,2
 mov api_phase,0
 mov api_resume,OFFSET named_2_go
 jmp named_capture
named_2_go:
 mov DWORD PTR [esp],OFFSET named_2_return
 jmp DWORD PTR named_targets[8]
named_2_return:
 mov api_kind,2
 mov api_phase,1
 mov api_resume,OFFSET named_2_done
 jmp named_capture
named_2_done:
 jmp DWORD PTR named_returns[8]
named_API_2 ENDP
named_API_3 PROC
 mov api_kind,3
 mov api_phase,0
 mov api_resume,OFFSET named_3_go
 jmp named_capture
named_3_go:
 mov DWORD PTR [esp],OFFSET named_3_return
 jmp DWORD PTR named_targets[12]
named_3_return:
 mov api_kind,3
 mov api_phase,1
 mov api_resume,OFFSET named_3_done
 jmp named_capture
named_3_done:
 jmp DWORD PTR named_returns[12]
named_API_3 ENDP
END
