.386
.model flat, C
option casemap:none
EXTERN m2_input:BYTE
EXTERN m2_output:BYTE
EXTERN m2_host_esp:DWORD
PUBLIC m2_enter
PUBLIC m2_capture
.code
m2_enter PROC
 pushfd
 pushad
 mov m2_host_esp, esp
 push DWORD PTR m2_input[32]
 popfd
 mov eax,DWORD PTR m2_input[0]
 mov ecx,DWORD PTR m2_input[4]
 mov edx,DWORD PTR m2_input[8]
 mov ebx,DWORD PTR m2_input[12]
 mov ebp,DWORD PTR m2_input[20]
 mov esi,DWORD PTR m2_input[24]
 mov edi,DWORD PTR m2_input[28]
 mov esp,DWORD PTR m2_input[16]
 jmp DWORD PTR m2_input[36]
m2_enter ENDP
m2_capture PROC
 mov DWORD PTR m2_output[0],eax
 mov DWORD PTR m2_output[4],ecx
 mov DWORD PTR m2_output[8],edx
 mov DWORD PTR m2_output[12],ebx
 mov DWORD PTR m2_output[16],esp
 mov DWORD PTR m2_output[20],ebp
 mov DWORD PTR m2_output[24],esi
 mov DWORD PTR m2_output[28],edi
 mov esp,m2_host_esp
 pushfd
 pop DWORD PTR m2_output[32]
 mov DWORD PTR m2_output[36],10000100h
 popad
 popfd
 ret
m2_capture ENDP
END
