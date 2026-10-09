; Authored natural-stack observation scaffold. Original provider bytes remain
; in admitted private pages, and its API calls use the real Windows stack/IAT.
.686p
.xmm
.model flat, C
option casemap:none
ASSUME FS:NOTHING
EXTERN fd_input:BYTE
EXTERN fd_before:BYTE
EXTERN fd_after:BYTE
EXTERN fd_saved_esp:DWORD
EXTERN fd_writer_sp:DWORD
EXTERN fd_stack_base:DWORD
EXTERN fd_stack_bytes:DWORD
EXTERN fd_stack_limit:DWORD
EXTERN fd_stack_top:DWORD
EXTERN fd_limit_after:DWORD
EXTERN fd_top_after:DWORD
EXTERN fd_capture_complete:DWORD
EXTERN fd_entry_complete:DWORD
EXTERN fd_guest_fx:BYTE
EXTERN fd_guest_env:BYTE
EXTERN fd_host_fx:BYTE
EXTERN fd_host_after:BYTE
EXTERN fd_fx_before:BYTE
EXTERN fd_fx_after:BYTE
EXTERN fd_host_env:BYTE
EXTERN fd_host_env_after:BYTE
EXTERN fd_env_before:BYTE
EXTERN fd_env_after:BYTE
EXTERN fd_stack_before:BYTE
EXTERN fd_stack_after:BYTE
EXTERN fd_pages_before:BYTE
EXTERN fd_pages_after:BYTE
EXTERN fd_page_addresses:DWORD
EXTERN fd_scratch_esp:DWORD
EXTERN fd_flags_temp:DWORD
PUBLIC fd_enter
PUBLIC fd_capture
PUBLIC fd_restore
.code
; REP copies happen outside source BEFORE/AFTER CPU observations. The actual
; guest stack is never used as temporary PUSHFD storage or as a copy target.
copy_pages MACRO destination
 LOCAL page_loop
 mov ebx,OFFSET destination
 mov edx,OFFSET fd_page_addresses
 mov eax,7
page_loop:
 mov esi,DWORD PTR [edx]
 mov edi,ebx
 mov ecx,1024
 cld
 rep movsd
 add ebx,4096
 add edx,4
 dec eax
 jnz page_loop
ENDM
fd_enter PROC
 pushfd
 pushad
 mov fd_saved_esp,esp
 fxsave fd_host_fx
 fnstenv fd_host_env
 ; Preserve the exact host state while checking the real thread stack bounds.
 fldenv fd_host_env
 mov eax,esp
 sub eax,4
 mov fd_writer_sp,eax
 cmp eax,fd_stack_limit
 jb admission_failed
 mov edx,eax
 sub edx,256
 jc admission_failed
 cmp edx,fd_stack_limit
 jb admission_failed
 cmp eax,fd_stack_top
 jae admission_failed
 push 10000100h
 ; This is the natural next CALL frame on the current Windows thread stack.
 ; It is an authored outer caller return word, not a rewritten source CALL.
 fxrstor fd_guest_fx
 fldenv fd_guest_env
 fxsave fd_fx_before
 fnstenv fd_env_before
 fldenv fd_env_before
 mov esi,fd_stack_base
 mov edi,OFFSET fd_stack_before
 mov ecx,fd_stack_bytes
 shr ecx,2
 cld
 rep movsd
 copy_pages fd_pages_before
 ; Seed every source GPR and arithmetic flag only after instrumentation copies.
 mov esp,fd_scratch_esp
 push DWORD PTR fd_input[32]
 popfd
 mov eax,DWORD PTR fd_input[0]
 mov ecx,DWORD PTR fd_input[4]
 mov edx,DWORD PTR fd_input[8]
 mov ebx,DWORD PTR fd_input[12]
 mov ebp,DWORD PTR fd_input[20]
 mov esi,DWORD PTR fd_input[24]
 mov edi,DWORD PTR fd_input[28]
 mov esp,fd_writer_sp
 mov DWORD PTR fd_before[0],eax
 mov DWORD PTR fd_before[4],ecx
 mov DWORD PTR fd_before[8],edx
 mov DWORD PTR fd_before[12],ebx
 mov DWORD PTR fd_before[16],esp
 mov DWORD PTR fd_before[20],ebp
 mov DWORD PTR fd_before[24],esi
 mov DWORD PTR fd_before[28],edi
 mov esp,fd_scratch_esp
 pushfd
 pop DWORD PTR fd_before[32]
 mov DWORD PTR fd_before[36],78004254h
 mov fd_entry_complete,1
 mov esp,fd_writer_sp
 jmp DWORD PTR fd_input[36]
admission_failed:
 mov esp,fd_saved_esp
 fxrstor fd_host_fx
 fldenv fd_host_env
 popad
 popfd
 ret
fd_enter ENDP
fd_capture PROC
 ; The original writer has naturally RET'd through the outer capture JMP.
 ; Only MOVs precede the CPU/PUSHFD/FXSAVE/FNSTENV observations.
 mov DWORD PTR fd_after[0],eax
 mov DWORD PTR fd_after[4],ecx
 mov DWORD PTR fd_after[8],edx
 mov DWORD PTR fd_after[12],ebx
 mov DWORD PTR fd_after[16],esp
 mov DWORD PTR fd_after[20],ebp
 mov DWORD PTR fd_after[24],esi
 mov DWORD PTR fd_after[28],edi
 mov esp,fd_scratch_esp
 pushfd
 pop DWORD PTR fd_after[32]
 mov DWORD PTR fd_after[36],10000100h
 fxsave fd_fx_after
 fnstenv fd_env_after
 ; NT_TIB limits are instrumentation metadata, sampled after architectural FP.
 mov eax,DWORD PTR fs:[8]
 mov fd_limit_after,eax
 mov eax,DWORD PTR fs:[4]
 mov fd_top_after,eax
 mov esi,fd_stack_base
 mov edi,OFFSET fd_stack_after
 mov ecx,fd_stack_bytes
 shr ecx,2
 cld
 rep movsd
 copy_pages fd_pages_after
 mov fd_capture_complete,1
 mov esp,fd_saved_esp
 fxrstor fd_host_fx
 fldenv fd_host_env
 fxsave fd_host_after
 fnstenv fd_host_env_after
 fldenv fd_host_env
 popad
 popfd
 ret
fd_capture ENDP
fd_restore PROC
 ; Host-only containment after a real hardware exception, never body success.
 fxrstor fd_host_fx
 fldenv fd_host_env
 ret
fd_restore ENDP
END
