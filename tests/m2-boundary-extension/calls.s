.intel_syntax noprefix
.text
.globl entry, after_direct, after_import, after_indirect, direct, timer, choice_add, choice_sub
entry:
  mov eax, dword ptr [esp+4]
  push eax
  mov eax, 0xa5a5f00d
  call direct
after_direct:
  add eax, dword ptr [0x21001000]
  mov dword ptr [0x21001004], eax
  call dword ptr [0x21001008]
after_import:
  mov edx, eax
  mov eax, dword ptr [esp+4]
  push eax
  call dword ptr [0x2100100c]
after_indirect:
  lea esp, [esp+4]
  mov dword ptr [0x2100105c], 7
  ret
.org 0x200
direct:
  push eax
  mov eax, dword ptr [esp+4]
  mov dword ptr [0x21001040], eax
  lea eax, [esp+4]
  mov dword ptr [0x21001044], eax
  pop eax
  mov eax, dword ptr [esp+4]
  add eax, ecx
  ret 4
.org 0x300
timer:
  push eax
  mov eax, dword ptr [esp+4]
  mov dword ptr [0x21001048], eax
  lea eax, [esp+4]
  mov dword ptr [0x2100104c], eax
  pop eax
  inc dword ptr [0x21001060]
  inc dword ptr [0x21001064]
  mov eax, dword ptr [0x21001010]
  ret
.org 0x400
choice_add:
  push eax
  mov eax, dword ptr [esp+4]
  mov dword ptr [0x21001050], eax
  lea eax, [esp+4]
  mov dword ptr [0x21001054], eax
  pop eax
  mov dword ptr [0x21001058], 0
  add eax, edx
  ret
.org 0x500
choice_sub:
  push eax
  mov eax, dword ptr [esp+4]
  mov dword ptr [0x21001050], eax
  lea eax, [esp+4]
  mov dword ptr [0x21001054], eax
  pop eax
  mov dword ptr [0x21001058], 1
  sub eax, edx
  ret
