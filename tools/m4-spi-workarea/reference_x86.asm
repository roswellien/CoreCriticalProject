.686p
.xmm
.model flat,C
option casemap:none
EXTERN spi_input:BYTE
EXTERN spi_before:BYTE
EXTERN spi_after:BYTE
EXTERN spi_host_esp:DWORD
EXTERN spi_guest_fx:BYTE
EXTERN spi_host_fx:BYTE
EXTERN spi_host_after:BYTE
EXTERN spi_fx_before:BYTE
EXTERN spi_fx_after:BYTE
EXTERN spi_env_before:BYTE
EXTERN spi_env_after:BYTE
EXTERN spi_host_env:BYTE
EXTERN spi_host_env_after:BYTE
EXTERN spi_service_before:BYTE
EXTERN spi_service_after:BYTE
EXTERN spi_service_fx_before:BYTE
EXTERN spi_service_fx_after:BYTE
EXTERN spi_service_env_before:BYTE
EXTERN spi_service_env_after:BYTE
EXTERN spi_service_rect_before:BYTE
EXTERN spi_service_rect_after:BYTE
EXTERN spi_service_esp:DWORD
EXTERN spi_actual_provider:DWORD
EXTERN spi_resume:DWORD
EXTERN spi_provider_esp_before:DWORD
EXTERN spi_provider_esp_after:DWORD
PUBLIC spi_enter
PUBLIC spi_capture
PUBLIC spi_restore
PUBLIC spi_service_entry
.code
spi_enter PROC
 pushfd
 pushad
 mov spi_host_esp,esp
 fxsave spi_host_fx
 fnstenv spi_host_env
 fxrstor spi_guest_fx
 fxsave spi_fx_before
 fnstenv spi_env_before
 push DWORD PTR spi_input[32]
 popfd
 mov eax,DWORD PTR spi_input[0]
 mov ecx,DWORD PTR spi_input[4]
 mov edx,DWORD PTR spi_input[8]
 mov ebx,DWORD PTR spi_input[12]
 mov ebp,DWORD PTR spi_input[20]
 mov esi,DWORD PTR spi_input[24]
 mov edi,DWORD PTR spi_input[28]
 mov esp,DWORD PTR spi_input[16]
 mov DWORD PTR spi_before[0],eax
 mov DWORD PTR spi_before[4],ecx
 mov DWORD PTR spi_before[8],edx
 mov DWORD PTR spi_before[12],ebx
 mov DWORD PTR spi_before[16],esp
 mov DWORD PTR spi_before[20],ebp
 mov DWORD PTR spi_before[24],esi
 mov DWORD PTR spi_before[28],edi
 mov esp,spi_host_esp
 pushfd
 pop DWORD PTR spi_before[32]
 mov esp,DWORD PTR spi_input[36]
 mov DWORD PTR spi_before[36],esp
 mov esp,DWORD PTR spi_input[16]
 jmp DWORD PTR spi_input[36]
spi_enter ENDP
spi_service_entry PROC
 ; Capture actual import-entry state without flags-changing instructions.
 mov DWORD PTR spi_service_before[0],eax
 mov DWORD PTR spi_service_before[4],ecx
 mov DWORD PTR spi_service_before[8],edx
 mov DWORD PTR spi_service_before[12],ebx
 mov DWORD PTR spi_service_before[16],esp
 mov DWORD PTR spi_service_before[20],ebp
 mov DWORD PTR spi_service_before[24],esi
 mov DWORD PTR spi_service_before[28],edi
 mov spi_service_esp,esp
 mov DWORD PTR spi_service_before[36],00482cddh
 mov esp,spi_host_esp
 pushfd
 pop DWORD PTR spi_service_before[32]
 fxsave spi_service_fx_before
 fnstenv spi_service_env_before
 mov eax,DWORD PTR ds:[00608fa0h]
 mov DWORD PTR spi_service_rect_before[0],eax
 mov eax,DWORD PTR ds:[00608fa4h]
 mov DWORD PTR spi_service_rect_before[4],eax
 mov eax,DWORD PTR ds:[00608fa8h]
 mov DWORD PTR spi_service_rect_before[8],eax
 mov eax,DWORD PTR ds:[00608fach]
 mov DWORD PTR spi_service_rect_before[12],eax
 ; Windows provider runs on its actual thread stack. Copy only the four exact
 ; query arguments; the original guest CALL return word is left untouched.
 mov esp,spi_host_esp
 push 0
 push 00608fa0h
 push 0
 push 30h
 lea eax,[esp-4]
 mov spi_provider_esp_before,eax
 mov eax,DWORD PTR spi_service_before[0]
 mov ecx,DWORD PTR spi_service_before[4]
 mov edx,DWORD PTR spi_service_before[8]
 mov ebx,DWORD PTR spi_service_before[12]
 mov ebp,DWORD PTR spi_service_before[20]
 mov esi,DWORD PTR spi_service_before[24]
 mov edi,DWORD PTR spi_service_before[28]
 call DWORD PTR spi_actual_provider
spi_service_entry ENDP
spi_service_return PROC
 mov DWORD PTR spi_service_after[0],eax
 mov DWORD PTR spi_service_after[4],ecx
 mov DWORD PTR spi_service_after[8],edx
 mov DWORD PTR spi_service_after[12],ebx
 mov DWORD PTR spi_service_after[16],esp
 mov spi_provider_esp_after,esp
 mov DWORD PTR spi_service_after[20],ebp
 mov DWORD PTR spi_service_after[24],esi
 mov DWORD PTR spi_service_after[28],edi
 mov DWORD PTR spi_service_after[36],00482ce3h
 mov esp,spi_host_esp
 pushfd
 pop DWORD PTR spi_service_after[32]
 fxsave spi_service_fx_after
 fnstenv spi_service_env_after
 mov eax,DWORD PTR ds:[00608fa0h]
 mov DWORD PTR spi_service_rect_after[0],eax
 mov eax,DWORD PTR ds:[00608fa4h]
 mov DWORD PTR spi_service_rect_after[4],eax
 mov eax,DWORD PTR ds:[00608fa8h]
 mov DWORD PTR spi_service_rect_after[8],eax
 mov eax,DWORD PTR ds:[00608fach]
 mov DWORD PTR spi_service_rect_after[12],eax
 ; The actual captured providerESP must prove stdcall16 cleanup. The caller
 ; representation returns to its own independent diagnostic frame S-12.
 mov eax,spi_service_esp
 lea eax,[eax+20]
 mov DWORD PTR spi_service_after[16],eax
 mov eax,DWORD PTR spi_service_after[0]
 mov ecx,DWORD PTR spi_service_after[4]
 mov edx,DWORD PTR spi_service_after[8]
 mov ebx,DWORD PTR spi_service_after[12]
 mov ebp,DWORD PTR spi_service_after[20]
 mov esi,DWORD PTR spi_service_after[24]
 mov edi,DWORD PTR spi_service_after[28]
 mov esp,DWORD PTR spi_service_after[16]
 jmp DWORD PTR spi_resume
spi_service_return ENDP
spi_capture PROC
 mov DWORD PTR spi_after[0],eax
 mov DWORD PTR spi_after[4],ecx
 mov DWORD PTR spi_after[8],edx
 mov DWORD PTR spi_after[12],ebx
 mov DWORD PTR spi_after[16],esp
 mov DWORD PTR spi_after[20],ebp
 mov DWORD PTR spi_after[24],esi
 mov DWORD PTR spi_after[28],edi
 mov esp,spi_host_esp
 pushfd
 pop DWORD PTR spi_after[32]
 mov DWORD PTR spi_after[36],00482ff0h
 fxsave spi_fx_after
 fnstenv spi_env_after
 fxrstor spi_host_fx
 fldenv spi_host_env
 fxsave spi_host_after
 fnstenv spi_host_env_after
 fldenv spi_host_env
 popad
 popfd
 ret
spi_capture ENDP
spi_restore PROC
 fxrstor spi_host_fx
 fldenv spi_host_env
 fxsave spi_host_after
 fnstenv spi_host_env_after
 fldenv spi_host_env
 ret
spi_restore ENDP
END
